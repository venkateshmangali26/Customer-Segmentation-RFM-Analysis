"""
Comprehensive Visualization Module for Customer Segmentation & RFM Analysis.
Produces publication-quality figures:
- Feature distribution (raw vs log)
- Correlation heatmap
- Clustering evaluation curves (Elbow & Silhouette)
- 2D PCA cluster scatter plot
- Marketing snake plot (standardized RFM profiles)
- Revenue vs Customer count share
- Campaign response rate lift comparison
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.config import FIGURES_DIR

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def plot_rfm_distributions(rfm_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "01_rfm_distributions.png"

    fig, axes = plt.subplots(3, 2, figsize=(14, 11))
    palette = ["#1f77b4", "#2ca02c", "#ff7f0e"]
    features = ["Recency", "Frequency", "Monetary"]

    for i, col in enumerate(features):
        sns.histplot(rfm_df[col], kde=True, ax=axes[i, 0], color=palette[i], bins=40, line_kws={"linewidth": 2})
        axes[i, 0].set_title(f"Raw {col} Distribution (Skew: {rfm_df[col].skew():.2f})", fontsize=12, fontweight="bold")
        axes[i, 0].set_xlabel(col, fontsize=10)
        axes[i, 0].set_ylabel("Count", fontsize=10)

        log_val = np.log1p(rfm_df[col])
        sns.histplot(log_val, kde=True, ax=axes[i, 1], color=palette[i], bins=40, line_kws={"linewidth": 2})
        axes[i, 1].set_title(f"Log1p({col}) Distribution (Skew: {log_val.skew():.2f})", fontsize=12, fontweight="bold")
        axes[i, 1].set_xlabel(f"log1p({col})", fontsize=10)
        axes[i, 1].set_ylabel("Count", fontsize=10)

    plt.suptitle("Feature Distributions Before and After Log-Transformation", fontsize=15, fontweight="bold", y=0.99)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    return save_path


def plot_correlation_heatmap(rfm_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "02_correlation_heatmap.png"

    cols = ["Recency", "Frequency", "Monetary", "AOV", "Tenure_Days", "UniqueProducts"]
    valid_cols = [c for c in cols if c in rfm_df.columns]
    corr = rfm_df[valid_cols].corr()

    plt.figure(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = sns.diverging_palette(220, 20, as_cmap=True)

    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1.0, vmin=-1.0, center=0, annot=True, fmt=".2f", square=True, linewidths=0.75, cbar_kws={"shrink": 0.8})
    plt.title("Correlation Matrix of Customer RFM & Behavioral Metrics", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    return save_path


def plot_clustering_evaluation(eval_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "03_clustering_evaluation_curves.png"

    fig, ax1 = plt.subplots(figsize=(10, 6))
    color_wcss = "#2b5c8f"
    color_sil = "#e24a4a"

    ax1.set_xlabel("Number of Clusters (k)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Inertia (Within-Cluster Sum of Squares)", color=color_wcss, fontsize=12, fontweight="bold")
    line1 = ax1.plot(eval_df["k"], eval_df["Inertia_WCSS"], marker="o", linewidth=2.5, color=color_wcss, label="Inertia / WCSS")
    ax1.tick_params(axis="y", labelcolor=color_wcss)
    ax1.set_xticks(eval_df["k"])

    ax2 = ax1.twinx()
    ax2.set_ylabel("Silhouette Score", color=color_sil, fontsize=12, fontweight="bold")
    line2 = ax2.plot(eval_df["k"], eval_df["Silhouette_Score"], marker="s", linewidth=2.5, linestyle="--", color=color_sil, label="Silhouette Score")
    ax2.tick_params(axis="y", labelcolor=color_sil)

    if 4 in eval_df["k"].values:
        ax1.axvline(x=4, color="#333333", linestyle=":", linewidth=1.8, label="Selected Optimal k = 4")

    lines = line1 + line2
    labels = [l.get_label() for l in lines] + ["Selected Optimal k = 4"]
    ax1.legend(lines + [plt.Line2D([0], [0], color="#333333", linestyle=":", linewidth=1.8)], labels, loc="upper right", frameon=True)

    plt.title("Elbow Method & Silhouette Analysis for Optimal k Selection", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    return save_path


def plot_pca_clusters_2d(rfm_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path_cluster = output_dir / "04_pca_clusters_2d.png"
    save_path_discrete = output_dir / "05_pca_discrete_feature_2d.png"

    persona_col = "Cluster_Persona" if "Cluster_Persona" in rfm_df.columns else "Cluster"

    # Plot 1: Hue = Cluster Persona
    plt.figure(figsize=(11, 8))
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    sns.scatterplot(
        data=rfm_df,
        x="PCA_1",
        y="PCA_2",
        hue=persona_col,
        palette=palette[: rfm_df[persona_col].nunique()],
        alpha=0.65,
        s=45,
        edgecolor="w",
        linewidth=0.3,
    )

    centers = rfm_df.groupby(persona_col)[["PCA_1", "PCA_2"]].mean()
    plt.scatter(
        centers["PCA_1"],
        centers["PCA_2"],
        color="black",
        s=180,
        marker="X",
        edgecolor="white",
        linewidth=1.5,
        label="Cluster Centroids",
        zorder=5,
    )

    plt.title("2D PCA Projection of Customer Clusters (K-Means)", fontsize=14, fontweight="bold")
    plt.xlabel("Principal Component 1 (81.0% Variance Explained)", fontsize=11, fontweight="bold")
    plt.ylabel("Principal Component 2 (14.9% Variance Explained)", fontsize=11, fontweight="bold")
    plt.legend(title="Customer Persona", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig(save_path_cluster, dpi=300, bbox_inches="tight")
    plt.close()

    # Plot 2: Discrete Hue
    discrete_col = "R_Score" if "R_Score" in rfm_df.columns else "Cluster"
    plt.figure(figsize=(11, 8))
    sns.scatterplot(
        data=rfm_df,
        x="PCA_1",
        y="PCA_2",
        hue=discrete_col,
        palette="viridis",
        alpha=0.65,
        s=45,
        edgecolor="w",
        linewidth=0.3,
    )
    plt.title(f"2D PCA Projection with Discrete Feature Hue ({discrete_col})", fontsize=14, fontweight="bold")
    plt.xlabel("Principal Component 1", fontsize=11, fontweight="bold")
    plt.ylabel("Principal Component 2", fontsize=11, fontweight="bold")
    plt.legend(title=discrete_col, bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig(save_path_discrete, dpi=300, bbox_inches="tight")
    plt.close()

    return save_path_cluster, save_path_discrete


def plot_snake_plot(rfm_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "06_snake_plot_rfm_profiles.png"

    persona_col = "Cluster_Persona" if "Cluster_Persona" in rfm_df.columns else "Cluster"
    features = ["Recency", "Frequency", "Monetary"]

    log_df = np.log1p(rfm_df[features])
    scaler = StandardScaler()
    scaled_df = pd.DataFrame(scaler.fit_transform(log_df), columns=features, index=rfm_df.index)
    scaled_df[persona_col] = rfm_df[persona_col]

    melted = pd.melt(
        scaled_df,
        id_vars=[persona_col],
        value_vars=features,
        var_name="Metric",
        value_name="Normalized_Value",
    )

    plt.figure(figsize=(10, 6))
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    sns.lineplot(
        data=melted,
        x="Metric",
        y="Normalized_Value",
        hue=persona_col,
        marker="o",
        markersize=9,
        linewidth=2.5,
        palette=palette[: rfm_df[persona_col].nunique()],
        errorbar=None,
    )

    plt.axhline(0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    plt.title("Customer Segment Behavioral Profiles (Snake Plot)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("RFM Feature", fontsize=11, fontweight="bold")
    plt.ylabel("Standardized Relative Value (Z-Score)", fontsize=11, fontweight="bold")
    plt.legend(title="Customer Persona", frameon=True, loc="best")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    return save_path


def plot_revenue_vs_customer_share(profile_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "07_revenue_vs_customers_pareto.png"

    df_plot = profile_df.copy()
    persona_col = "Cluster_Persona" if "Cluster_Persona" in df_plot.columns else "Cluster"

    x = np.arange(len(df_plot))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 6))
    rects1 = ax.bar(x - width / 2, df_plot["CustomerSharePct"], width, label="Customer Share (%)", color="#4a90e2")
    rects2 = ax.bar(x + width / 2, df_plot["RevenueSharePct"], width, label="Revenue Share (%)", color="#50e3c2")

    ax.set_ylabel("Percentage (%)", fontsize=12, fontweight="bold")
    ax.set_title("Customer Share vs. Revenue Contribution by Segment (Pareto Disparity)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot[persona_col], rotation=15, ha="right", fontsize=10, fontweight="bold")
    ax.legend(frameon=True, fontsize=11)

    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f"{height:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    for rect in rects2:
        height = rect.get_height()
        ax.annotate(f"{height:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    return save_path


def plot_campaign_lift_comparison(rollout_df: pd.DataFrame, output_dir: Optional[Path] = FIGURES_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "08_campaign_response_lift.png"

    df_plot = rollout_df.copy()
    x = np.arange(len(df_plot))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 6))
    rects1 = ax.bar(x - width / 2, df_plot["Baseline_Response_Rate_Pct"], width, label="Baseline Blanket Campaign (%)", color="#b0bec5")
    rects2 = ax.bar(x + width / 2, df_plot["Targeted_Response_Rate_Pct"], width, label="Targeted Segment Campaign (%)", color="#e91e63")

    ax.set_ylabel("Response / Conversion Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Marketing Campaign Response Rates: Blanket Blast vs. Targeted Segment Outreach", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot["Segment_Persona"], rotation=15, ha="right", fontsize=10, fontweight="bold")
    ax.legend(frameon=True, fontsize=11)

    for i, row in df_plot.iterrows():
        lift = row["Relative_Response_Lift_Pct"]
        h = row["Targeted_Response_Rate_Pct"]
        ax.annotate(f"+{lift:.0f}% Lift", xy=(x[i] + width / 2, h),
                    xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#c2185b")

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    return save_path


def generate_all_visualizations(
    rfm_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    rollout_df: pd.DataFrame,
    output_dir: Optional[Path] = FIGURES_DIR,
) -> Dict[str, Path]:
    figures = {}
    print("Generating publication-ready figures...")
    figures["distributions"] = plot_rfm_distributions(rfm_df, output_dir)
    figures["correlation"] = plot_correlation_heatmap(rfm_df, output_dir)
    figures["evaluation"] = plot_clustering_evaluation(eval_df, output_dir)
    pca_c, pca_d = plot_pca_clusters_2d(rfm_df, output_dir)
    figures["pca_clusters"] = pca_c
    figures["pca_discrete"] = pca_d
    figures["snake_plot"] = plot_snake_plot(rfm_df, output_dir)
    figures["pareto"] = plot_revenue_vs_customer_share(profile_df, output_dir)
    figures["campaign_lift"] = plot_campaign_lift_comparison(rollout_df, output_dir)
    print(f"Generated {len(figures)} figures saved to {output_dir}")
    return figures
