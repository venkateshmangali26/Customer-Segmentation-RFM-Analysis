"""Tests for src/clustering.py — KMeans + PCA + persona labeling."""
import numpy as np
import pandas as pd
import pytest

from src.data_generator import generate_synthetic_transactions
from src.data_processing import clean_transactions
from src.rfm_analysis import run_rfm_pipeline
from src.clustering import (
    preprocess_rfm_for_clustering,
    evaluate_cluster_range,
    train_kmeans_clustering,
    apply_pca_reduction,
    interpret_and_label_clusters,
    run_clustering_pipeline,
)


@pytest.fixture(scope="module")
def rfm_df():
    raw = generate_synthetic_transactions(n_transactions=3000, n_customers=150, output_path=None)
    cleaned, _ = clean_transactions(raw, output_path=None)
    rfm, _ = run_rfm_pipeline(cleaned, output_path=None)
    return rfm


def test_preprocess_rfm_for_clustering_returns_scaled_array(rfm_df):
    scaled_array, scaled_df, scaler, skew_info = preprocess_rfm_for_clustering(rfm_df)
    assert scaled_array.shape[0] == len(rfm_df)
    assert scaled_array.shape[1] == 3  # R, F, M
    assert isinstance(scaled_df, pd.DataFrame)
    assert hasattr(scaler, "transform")  # StandardScaler
    assert "features" in skew_info
    assert "initial_skewness" in skew_info
    assert "post_log_skewness" in skew_info
    # Log + standardize should produce mean ~0, std ~1
    np.testing.assert_allclose(scaled_array.mean(axis=0), 0, atol=1e-7)
    np.testing.assert_allclose(scaled_array.std(axis=0), 1, atol=1e-7)


def test_evaluate_cluster_range_produces_metrics_for_each_k(rfm_df):
    scaled_array, _, _, _ = preprocess_rfm_for_clustering(rfm_df)
    eval_df = evaluate_cluster_range(scaled_array, k_min=2, k_max=5)
    assert len(eval_df) == 4  # k=2..5
    expected_cols = {"k", "Inertia_WCSS", "Silhouette_Score",
                     "Davies_Bouldin_Index", "Calinski_Harabasz_Score"}
    assert expected_cols.issubset(eval_df.columns)
    # All metrics should be finite
    for col in ["Inertia_WCSS", "Silhouette_Score", "Davies_Bouldin_Index", "Calinski_Harabasz_Score"]:
        assert eval_df[col].apply(np.isfinite).all(), f"{col} has non-finite values"


def test_train_kmeans_clustering_returns_labels(rfm_df):
    scaled_array, _, _, _ = preprocess_rfm_for_clustering(rfm_df)
    model, labels = train_kmeans_clustering(scaled_array, n_clusters=4)
    assert len(labels) == len(rfm_df)
    # Labels should be in [0, 3]
    assert set(np.unique(labels)).issubset({0, 1, 2, 3})
    # Should have at least 2 distinct clusters
    assert len(np.unique(labels)) >= 2


def test_apply_pca_reduction_returns_3_components(rfm_df):
    scaled_array, _, _, _ = preprocess_rfm_for_clustering(rfm_df)
    pca_coords, pca_model, loadings = apply_pca_reduction(scaled_array, ["Recency", "Frequency", "Monetary"])
    assert pca_coords.shape == (len(rfm_df), 3)
    assert hasattr(pca_model, "explained_variance_ratio_")
    # Cumulative explained variance should be <= 1.0
    assert pca_model.explained_variance_ratio_.sum() <= 1.0 + 1e-9
    # Loadings DataFrame has the feature names as index
    assert set(loadings.index) == {"Recency", "Frequency", "Monetary"}


def test_interpret_and_label_clusters_assigns_known_personas(rfm_df):
    # Need a copy because clustering modifies in-place
    rfm_with_cluster = rfm_df.copy()
    scaled_array, _, _, _ = preprocess_rfm_for_clustering(rfm_with_cluster)
    _, labels = train_kmeans_clustering(scaled_array, n_clusters=4)
    rfm_with_cluster["Cluster"] = labels
    labeled_df, profile_df, cluster_names = interpret_and_label_clusters(rfm_with_cluster)
    # Cluster_Persona column should be present
    assert "Cluster_Persona" in labeled_df.columns
    # Should assign at least VIP Champions and Hibernating
    expected_personas = {"VIP Champions", "Hibernating / One-Time Buyers"}
    actual_personas = set(labeled_df["Cluster_Persona"].unique())
    assert expected_personas.issubset(actual_personas)
    # profile_df should have summary stats per cluster
    assert "CustomerCount" in profile_df.columns
    assert "TotalRevenue" in profile_df.columns
    assert len(profile_df) == len(cluster_names)


def test_run_clustering_pipeline_end_to_end(rfm_df):
    rfm_labeled, profile_df, eval_df, pca_model, kmeans_model = run_clustering_pipeline(
        rfm_df, n_clusters=4, output_path=None
    )
    assert "Cluster" in rfm_labeled.columns
    assert "Cluster_Persona" in rfm_labeled.columns
    assert "PCA_1" in rfm_labeled.columns
    assert "PCA_2" in rfm_labeled.columns
    assert "PCA_3" in rfm_labeled.columns
    assert len(profile_df) == 4  # one row per cluster
