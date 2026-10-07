"""
Machine Learning Customer Segmentation Module.
Performs skewness transformation, feature scaling, optimal k evaluation (Elbow & Silhouette),
K-Means clustering, PCA dimensionality reduction, and customer persona profiling.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.config import (
    CLUSTER_METRICS_FILE,
    DEFAULT_OPTIMAL_K,
    K_MAX,
    K_MIN,
    RANDOM_SEED,
    REPORTS_DIR,
    RFM_DATA_FILE,
)


def preprocess_rfm_for_clustering(
    rfm_df: pd.DataFrame,
    features: Optional[List[str]] = None,
) -> Tuple[np.ndarray, pd.DataFrame, StandardScaler, Dict]:
    """Applies log transformation (np.log1p) and StandardScaler to RFM features."""
    if features is None:
        features = ["Recency", "Frequency", "Monetary"]

    raw_features = rfm_df[features].copy()
    initial_skew = {col: round(float(stats.skew(raw_features[col])), 3) for col in features}

    log_transformed = np.log1p(raw_features)
    post_log_skew = {col: round(float(stats.skew(log_transformed[col])), 3) for col in features}

    scaler = StandardScaler()
    scaled_array = scaler.fit_transform(log_transformed)
    scaled_df = pd.DataFrame(scaled_array, columns=[f"{col}_scaled" for col in features], index=rfm_df.index)

    skew_info = {
        "features": features,
        "initial_skewness": initial_skew,
        "post_log_skewness": post_log_skew,
    }

    return scaled_array, scaled_df, scaler, skew_info


def evaluate_cluster_range(
    scaled_features: np.ndarray,
    k_min: int = K_MIN,
    k_max: int = K_MAX,
    random_state: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Evaluates KMeans clustering performance across a range of k values."""
    results = []

    for k in range(k_min, k_max + 1):
        kmeans = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=random_state,
        )
        labels = kmeans.fit_predict(scaled_features)

        inertia = kmeans.inertia_
        sil = silhouette_score(
            scaled_features,
            labels,
            sample_size=min(1500, len(scaled_features)),
            random_state=random_state,
        )
        db_index = davies_bouldin_score(scaled_features, labels)
        ch_score = calinski_harabasz_score(scaled_features, labels)

        results.append({
            "k": k,
            "Inertia_WCSS": round(float(inertia), 2),
            "Silhouette_Score": round(float(sil), 4),
            "Davies_Bouldin_Index": round(float(db_index), 4),
            "Calinski_Harabasz_Score": round(float(ch_score), 2),
        })

    eval_df = pd.DataFrame(results)
    eval_file = REPORTS_DIR / "clustering_evaluation_metrics.csv"
    eval_file.parent.mkdir(parents=True, exist_ok=True)
    eval_df.to_csv(eval_file, index=False)

    return eval_df


def train_kmeans_clustering(
    scaled_features: np.ndarray,
    n_clusters: int = DEFAULT_OPTIMAL_K,
    random_state: int = RANDOM_SEED,
) -> Tuple[KMeans, np.ndarray]:
    """Fits KMeans clustering model with optimal number of clusters."""
    model = KMeans(
        n_clusters=n_clusters,
        init="k-means++",
        n_init=30,
        max_iter=500,
        random_state=random_state,
    )
    cluster_labels = model.fit_predict(scaled_features)
    return model, cluster_labels


def apply_pca_reduction(
    scaled_features: np.ndarray,
    feature_names: List[str],
    n_components: int = 3,
    random_state: int = RANDOM_SEED,
) -> Tuple[np.ndarray, PCA, pd.DataFrame]:
    """Computes PCA projections and feature loadings."""
    pca = PCA(n_components=n_components, random_state=random_state)
    pca_coords = pca.fit_transform(scaled_features)

    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f"PC{i+1}" for i in range(n_components)],
        index=feature_names,
    ).round(4)

    return pca_coords, pca, loadings


def interpret_and_label_clusters(
    rfm_df: pd.DataFrame,
    cluster_col: str = "Cluster",
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[int, str]]:
    """Profiles clusters based on RFM statistics and assigns distinct business personas."""
    df = rfm_df.copy()
    grouped = df.groupby(cluster_col).agg(
        Mean_Recency=("Recency", "mean"),
        Mean_Frequency=("Frequency", "mean"),
        Mean_Monetary=("Monetary", "mean"),
    ).reset_index()

    cluster_names = {}
    vip_cluster = grouped.sort_values("Mean_Monetary", ascending=False).iloc[0][cluster_col]
    cluster_names[int(vip_cluster)] = "VIP Champions"

    remaining = grouped[grouped[cluster_col] != vip_cluster].copy()
    hibernating_cluster = remaining.sort_values(["Mean_Monetary", "Mean_Recency"], ascending=[True, False]).iloc[0][cluster_col]
    cluster_names[int(hibernating_cluster)] = "Hibernating / One-Time Buyers"

    remaining = remaining[remaining[cluster_col] != hibernating_cluster].copy()
    if len(remaining) > 0:
        sorted_rem = remaining.sort_values("Mean_Recency", ascending=True)
        loyal_cluster = sorted_rem.iloc[0][cluster_col]
        cluster_names[int(loyal_cluster)] = "Loyal Regulars"

        if len(sorted_rem) > 1:
            at_risk_cluster = sorted_rem.iloc[1][cluster_col]
            cluster_names[int(at_risk_cluster)] = "At-Risk Lapsed Spenders"

        for _, extra_row in sorted_rem.iloc[2:].iterrows():
            c_val = int(extra_row[cluster_col])
            cluster_names[c_val] = f"Cluster {c_val} (Niche)"

    df["Cluster_Persona"] = df[cluster_col].map(cluster_names)

    total_rev = df["Monetary"].sum()
    total_cust = len(df)

    profile_df = (
        df.groupby(["Cluster", "Cluster_Persona"])
        .agg(
            CustomerCount=("CustomerID", "count"),
            TotalRevenue=("Monetary", "sum"),
            AvgRecency=("Recency", "mean"),
            AvgFrequency=("Frequency", "mean"),
            AvgMonetary=("Monetary", "mean"),
            AvgAOV=("AOV", "mean"),
            AvgTenure=("Tenure_Days", "mean"),
        )
        .reset_index()
    )

    profile_df["CustomerSharePct"] = (profile_df["CustomerCount"] / total_cust * 100).round(2)
    profile_df["RevenueSharePct"] = (profile_df["TotalRevenue"] / total_rev * 100).round(2)
    profile_df["AvgRecency"] = profile_df["AvgRecency"].round(1)
    profile_df["AvgFrequency"] = profile_df["AvgFrequency"].round(1)
    profile_df["AvgMonetary"] = profile_df["AvgMonetary"].round(2)
    profile_df["AvgAOV"] = profile_df["AvgAOV"].round(2)
    profile_df["AvgTenure"] = profile_df["AvgTenure"].round(1)
    profile_df["TotalRevenue"] = profile_df["TotalRevenue"].round(2)

    profile_df = profile_df.sort_values("TotalRevenue", ascending=False).reset_index(drop=True)

    CLUSTER_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    profile_df.to_csv(CLUSTER_METRICS_FILE, index=False)

    return df, profile_df, cluster_names


def run_clustering_pipeline(
    rfm_df: pd.DataFrame,
    n_clusters: int = DEFAULT_OPTIMAL_K,
    output_path: Optional[Path] = RFM_DATA_FILE,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, PCA, KMeans]:
    """Executes complete unsupervised clustering workflow."""
    feature_cols = ["Recency", "Frequency", "Monetary"]
    scaled_array, scaled_df, scaler, skew_info = preprocess_rfm_for_clustering(rfm_df, feature_cols)

    eval_df = evaluate_cluster_range(scaled_array, k_min=K_MIN, k_max=K_MAX)
    kmeans_model, labels = train_kmeans_clustering(scaled_array, n_clusters=n_clusters)
    rfm_df["Cluster"] = labels

    pca_coords, pca_model, loadings = apply_pca_reduction(scaled_array, feature_cols, n_components=3)
    rfm_df["PCA_1"] = pca_coords[:, 0].round(4)
    rfm_df["PCA_2"] = pca_coords[:, 1].round(4)
    rfm_df["PCA_3"] = pca_coords[:, 2].round(4)

    rfm_labeled, profile_df, cluster_names = interpret_and_label_clusters(rfm_df)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rfm_labeled.to_csv(output_path, index=False)
        print(f"Clustering complete: {n_clusters} clusters identified and saved to {output_path}")

    return rfm_labeled, profile_df, eval_df, pca_model, kmeans_model


if __name__ == "__main__":
    from src.data_processing import load_raw_data, clean_transactions
    from src.rfm_analysis import run_rfm_pipeline

    raw_df = load_raw_data()
    cleaned_df, _ = clean_transactions(raw_df)
    rfm_df, _ = run_rfm_pipeline(cleaned_df)
    rfm_clustered, profiles, eval_metrics, pca, kmeans = run_clustering_pipeline(rfm_df)

    print("\n--- Clustering Evaluation Metrics (k=2..9) ---")
    print(eval_metrics.to_string(index=False))
    print("\n--- K-Means Cluster Profiles ---")
    print(profiles.to_string(index=False))
