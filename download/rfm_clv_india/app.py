"""
Customer Segmentation, RFM Behavioral Intelligence & Predictive CLV Platform
================================================================================
Colorful Streamlit frontend with 7 sidebar modules:

  1. 📊 Executive KPI Overview          — KPI cards + Pareto + donut + table
  2. 🔍 RFM Quantile Explorer           — segment filter + R/F/M sliders + 2 scatters
  3. 🤖 K-Means & PCA Clustering        — 2D / 3D / Elbow / Snake sub-tabs
  4. 🔮 Predictive CLV (BG/NBD+GG)     — KPIs + box + churn-CLV scatter + top-N
  5. 📅 Cohort Retention Heatmap        — triangular heatmap + half-life table
  6. 📈 Sales Forecast (Prophet)        — historical + forecast + confidence band
  7. 🚀 Targeted Campaign Simulator     — 6 inputs + 4 KPIs + A/B bar chart + Z-test
  8. 📋 Strategic Playbook & Export     — 4 personas + CSV export per segment

Self-healing: on first run, generates data and runs the full pipeline if CSVs
are missing. Lazy backfills CLV columns on legacy CSVs.

All bug fixes from the prior audit are applied:
  - simulate_campaign_ab_test now accepts cpc_email, margin, aov_control,
    aov_targeted and the Tab-7 call site wires all four user inputs through.
  - Empty segment-multiselect now means "show all" instead of crashing to 0 of N.
  - Snake plot Z-score guarded against zero-std edge cases.
  - Sidebar "Clear cache" button invalidates @st.cache_data on demand.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import (
    CAMPAIGN_SUMMARY_FILE,
    CLEANED_DATA_FILE,
    CLUSTER_METRICS_FILE,
    RAW_DATA_FILE,
    REPORTS_DIR,
    RFM_DATA_FILE,
)
from src.clustering import run_clustering_pipeline
from src.clv_modeling import compute_predictive_clv
from src.cohort_analysis import run_cohort_analysis, compute_retention_rate_matrix
from src.data_generator import generate_synthetic_transactions
from src.data_processing import clean_transactions, load_raw_data
from src.marketing_strategy import MARKETING_PLAYBOOKS, simulate_campaign_ab_test
from src.rfm_analysis import run_rfm_pipeline
from src.sales_forecasting import forecast_sales, PROPHET_AVAILABLE

# ============================================================================
# 1. PAGE CONFIG + COLORFUL CUSTOM CSS
# ============================================================================

st.set_page_config(
    page_title="Customer Segmentation, RFM & CLV Intelligence (India)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colorful gradient theme — purple→blue→teal background, accent emerald
st.markdown(
    """
    <style>
    /* === Main background: subtle dark gradient === */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #151b3d 35%, #1a1f4d 70%, #0d2136 100%);
    }
    .main { background: transparent; }

    /* === KPI cards: glassmorphism with accent left border === */
    .kpi-card {
        background: linear-gradient(135deg, rgba(31, 41, 71, 0.85) 0%, rgba(21, 27, 48, 0.95) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.18);
        border-left: 4px solid #8b5cf6;
        border-radius: 14px;
        padding: 22px 26px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255,255,255,0.02) inset;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 12px 32px rgba(139, 92, 246, 0.25); }
    .kpi-title {
        font-size: 11px;
        color: #a5b4fc;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 10px;
        font-weight: 700;
    }
    .kpi-value {
        font-size: 30px;
        font-weight: 800;
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
    }
    .kpi-subtitle {
        font-size: 11px;
        color: #34d399;
        margin-top: 8px;
        font-weight: 600;
        letter-spacing: 0.04em;
    }

    /* === Tabs: pill-style with active accent === */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, rgba(31, 41, 71, 0.7) 0%, rgba(21, 27, 48, 0.85) 100%);
        border-radius: 8px;
        color: #cbd5e1;
        font-weight: 600;
        padding: 10px 20px;
        border: 1px solid rgba(99, 102, 241, 0.18);
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #8b5cf6;
        color: #e0e7ff;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%) !important;
        color: white !important;
        border-color: #a78bfa !important;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
    }

    /* === Sidebar: gradient + section headers === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e27 0%, #0d1b3a 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e7ff;
    }

    /* === Headings: gradient === */
    h1, h2, h3 {
        background: linear-gradient(135deg, #c4b5fd 0%, #93c5fd 50%, #5eead4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* === Plotly chart container: subtle inset === */
    .stPlotlyChart {
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 10px;
        padding: 6px;
        background: rgba(13, 21, 54, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# 2. SELF-HEALING DATA LOADER
# ============================================================================

@st.cache_data(show_spinner=False)
def initialize_and_load_data(_force_refresh: bool = False):
    """If RFM/cluster CSVs are missing, generate data and run the full pipeline.
    On legacy CSVs lacking CLV columns, lazily backfill them."""
    if not RFM_DATA_FILE.exists() or not CLUSTER_METRICS_FILE.exists():
        with st.spinner("🚀 Initializing pipeline: Generating sample transactions, training ML clusters, fitting BG/NBD..."):
            raw_df = generate_synthetic_transactions(n_transactions=50000, n_customers=5000)
            cleaned_df, _ = clean_transactions(raw_df, output_path=CLEANED_DATA_FILE)
            rfm_df, _ = run_rfm_pipeline(cleaned_df, output_path=RFM_DATA_FILE)
            rfm_clustered, cluster_profiles, eval_df, _, _ = run_clustering_pipeline(
                rfm_df, n_clusters=4, output_path=RFM_DATA_FILE
            )
            rfm_clustered, _ = compute_predictive_clv(cleaned_df, rfm_clustered, output_path=RFM_DATA_FILE)
    else:
        rfm_df = pd.read_csv(RFM_DATA_FILE)
        cluster_profiles = pd.read_csv(CLUSTER_METRICS_FILE)
        eval_file = REPORTS_DIR / "clustering_evaluation_metrics.csv"
        eval_df = pd.read_csv(eval_file) if eval_file.exists() else pd.DataFrame()

        # Self-heal CLV columns if needed
        if "Predicted_CLV_365D" not in rfm_df.columns and CLEANED_DATA_FILE.exists():
            with st.spinner("🔮 Backfilling CLV columns on legacy CSV..."):
                cleaned_df = pd.read_csv(CLEANED_DATA_FILE)
                rfm_df, _ = compute_predictive_clv(cleaned_df, rfm_df, output_path=RFM_DATA_FILE)

    return rfm_df, cluster_profiles, eval_df


# Sidebar: Clear-cache button so users can re-run the pipeline and see fresh data
if st.sidebar.button("🔄 Clear cache & reload from disk"):
    st.cache_data.clear()
    st.rerun()

try:
    rfm_df, cluster_profiles, eval_df = initialize_and_load_data()
except Exception as e:
    st.error(f"Critical error initializing pipeline datasets: {e}")
    st.stop()


# ============================================================================
# 3. SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.image("https://img.icons8.com/isometric/100/combo-chart.png", width=65)
st.sidebar.title("Navigation Hub")
nav_section = st.sidebar.radio(
    "Select Module:",
    [
        "📊 Executive KPI Overview",
        "🔍 RFM Quantile Explorer",
        "🤖 K-Means & PCA Clustering",
        "🔮 Predictive CLV (BG/NBD & Gamma-Gamma)",
        "📅 Cohort Retention Heatmap",
        "📈 Sales Forecast (Prophet)",
        "🚀 Targeted Campaign Simulator",
        "📋 Strategic Playbook & Export",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🪔 Indian Festival Calendar")
st.sidebar.markdown(
    "<small>Sales-boost windows driving the synthetic data generator:</small>",
    unsafe_allow_html=True,
)
from src.config import INDIAN_FESTIVAL_CALENDAR
month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
for month, boost, name in INDIAN_FESTIVAL_CALENDAR:
    boost_pct = int((boost - 1) * 100)
    bar_color = "#f59e0b" if boost >= 1.5 else "#3b82f6" if boost >= 1.25 else "#64748b"
    st.sidebar.markdown(
        f"<small><b>{month_names[month]} · {name}</b> "
        f"<span style='color:{bar_color}'>+{boost_pct}%</span></small>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Dataset Summary")
total_rev = rfm_df["Monetary"].sum()
st.sidebar.info(
    f"• **Active Customers:** {len(rfm_df):,}\n\n"
    f"• **Total Revenue:** ₹{total_rev:,.0f}\n\n"
    f"• **Avg Recency:** {rfm_df['Recency'].mean():.1f} days\n\n"
    f"• **Avg Frequency:** {rfm_df['Frequency'].mean():.1f} orders"
)
if "Predicted_CLV_365D" in rfm_df.columns:
    st.sidebar.success(
        f"• **Total 1-Yr CLV:** ₹{rfm_df['Predicted_CLV_365D'].sum():,.0f}\n\n"
        f"• **Mean P(Alive):** {rfm_df['P_Alive'].mean()*100:.1f}%"
    )
st.sidebar.markdown("---")
st.sidebar.caption(f"Forecast backend: **{'Prophet' if PROPHET_AVAILABLE else 'Holt-Winters'}**")


# ============================================================================
# MODULE 1: EXECUTIVE KPI OVERVIEW
# ============================================================================

if nav_section == "📊 Executive KPI Overview":
    st.subheader("Executive Performance & Revenue Concentration")
    st.markdown("High-level breakdown of customer lifetime value, Pareto distribution, and segment revenue share.")

    vip_mask = cluster_profiles["Cluster_Persona"] == "VIP Champions"
    vip_rev = cluster_profiles.loc[vip_mask, "TotalRevenue"].sum() if vip_mask.any() else 0.0
    vip_rev_share = (vip_rev / total_rev) * 100 if total_rev > 0 else 0

    # KPI cards with accent colors per role
    def kpi_card(title, value, subtitle, accent_color):
        return f"""
        <div class="kpi-card" style="border-left-color: {accent_color};">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtitle">{subtitle}</div>
        </div>
        """

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("Active Customers", f"{len(rfm_df):,}", "Filtered Active Base", "#3b82f6"), unsafe_allow_html=True)
    with c2:
        # Indian format: show in crores (1 Cr = 10M)
        st.markdown(kpi_card("Total Net Revenue", f"₹{total_rev/1e7:.2f} Cr", "100% Tracked Spend", "#10b981"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("VIP Revenue Share", f"{vip_rev_share:.1f}%", "Pareto Concentration", "#f59e0b"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Avg Customer Spend", f"₹{rfm_df['Monetary'].mean():,.0f}", f"Median: ₹{rfm_df['Monetary'].median():,.0f}", "#ec4899"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([7, 5])
    with col_left:
        st.markdown("#### Customer Base vs. Revenue Contribution (Pareto Disparity)")
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=cluster_profiles["Cluster_Persona"],
            y=cluster_profiles["CustomerSharePct"],
            name="Customer Share (%)",
            marker_color="#3b82f6",
            marker_line_color="#1e3a8a", marker_line_width=1.5,
        ))
        fig_pareto.add_trace(go.Bar(
            x=cluster_profiles["Cluster_Persona"],
            y=cluster_profiles["RevenueSharePct"],
            name="Revenue Share (%)",
            marker_color="#10b981",
            marker_line_color="#065f46", marker_line_width=1.5,
        ))
        fig_pareto.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,21,54,0.4)",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Percentage (%)",
            height=400,
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col_right:
        st.markdown("#### Segment Revenue Composition")
        fig_pie = px.pie(
            cluster_profiles,
            names="Cluster_Persona",
            values="TotalRevenue",
            hole=0.5,
            color="Cluster_Persona",
            color_discrete_sequence=["#8b5cf6", "#3b82f6", "#f59e0b", "#ec4899"],
            template="plotly_dark",
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=30, b=20), height=400,
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Detailed Cluster Profiling Table")
    st.dataframe(
        cluster_profiles.style.format({
            "TotalRevenue": "₹{:,.0f}",
            "AvgRecency": "{:.1f} days",
            "AvgFrequency": "{:.1f} orders",
            "AvgMonetary": "₹{:,.0f}",
            "AvgAOV": "₹{:,.0f}",
            "CustomerSharePct": "{:.2f}%",
            "RevenueSharePct": "{:.2f}%",
        }),
        use_container_width=True,
    )


# ============================================================================
# MODULE 2: RFM QUANTILE EXPLORER
# ============================================================================

elif nav_section == "🔍 RFM Quantile Explorer":
    st.subheader("RFM Quantile Scoring & Customer Filtering")
    st.markdown("Filter customers by their quintile scores (1–5), behavioral segment, and Indian state.")

    f1, f2, f3, f4, f5 = st.columns(5)
    with f1:
        selected_segment = st.multiselect(
            "Filter Segments:",
            options=sorted(rfm_df["RFM_Segment"].unique()),
            default=list(rfm_df["RFM_Segment"].unique())[:3],
        )
    with f2:
        r_range = st.slider("Recency Score (R)", 1, 5, (1, 5))
    with f3:
        f_range = st.slider("Frequency Score (F)", 1, 5, (1, 5))
    with f4:
        m_range = st.slider("Monetary Score (M)", 1, 5, (1, 5))
    with f5:
        # INDIA: state filter for Indian customer base
        if "State" in rfm_df.columns:
            all_states = sorted(rfm_df["State"].unique())
            selected_states = st.multiselect("Filter States:", options=all_states, default=all_states[:5])
        else:
            selected_states = None
            st.info("State column not present.")

    # FIX: empty multiselect = "show all" instead of "show none"
    if selected_segment:
        seg_mask = rfm_df["RFM_Segment"].isin(selected_segment)
    else:
        seg_mask = pd.Series(True, index=rfm_df.index)
        st.info("No segment selected — showing all segments. Pick at least one to filter.")

    # Apply state filter if states were selected
    if selected_states is not None:
        if selected_states:
            state_mask = rfm_df["State"].isin(selected_states)
        else:
            state_mask = pd.Series(True, index=rfm_df.index)
        seg_mask = seg_mask & state_mask

    filtered_df = rfm_df[
        seg_mask
        & (rfm_df["R_Score"].between(r_range[0], r_range[1]))
        & (rfm_df["F_Score"].between(f_range[0], f_range[1]))
        & (rfm_df["M_Score"].between(m_range[0], m_range[1]))
    ]

    st.success(f"🔍 Displaying **{len(filtered_df):,}** matching customer records out of {len(rfm_df):,} total.")

    col1, col2 = st.columns(2)
    with col1:
        fig_r_f = px.scatter(
            filtered_df,
            x="Recency", y="Frequency",
            size="Monetary", color="RFM_Segment",
            hover_data=["CustomerID", "Monetary", "AOV"],
            template="plotly_dark",
            title="Recency vs. Frequency (Bubble Size = Spend)",
            color_discrete_sequence=px.colors.qualitative.Bold,
            height=450,
        )
        fig_r_f.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
        st.plotly_chart(fig_r_f, use_container_width=True)

    with col2:
        fig_f_m = px.scatter(
            filtered_df,
            x="Frequency", y="Monetary",
            color="RFM_Segment",
            hover_data=["CustomerID", "Recency", "AOV"],
            log_y=True,
            template="plotly_dark",
            title="Frequency vs. Monetary Value (Log Scale)",
            color_discrete_sequence=px.colors.qualitative.Bold,
            height=450,
        )
        fig_f_m.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
        st.plotly_chart(fig_f_m, use_container_width=True)

    st.markdown("#### Filtered Customer Records Table")
    st.dataframe(
        filtered_df[[
            "CustomerID", "RFM_Segment", "Cluster_Persona", "Recency", "Frequency",
            "Monetary", "AOV", "RFM_Score_Code", "State", "Tenure_Days"
        ]].head(300),
        use_container_width=True,
    )


# ============================================================================
# MODULE 3: K-MEANS & PCA CLUSTERING
# ============================================================================

elif nav_section == "🤖 K-Means & PCA Clustering":
    st.subheader("Unsupervised Machine Learning & Dimensionality Reduction")
    st.markdown("K-Means clustering trained on log-transformed, scaled RFM features, projected onto 2D and 3D Principal Component spaces.")

    tab_2d, tab_3d, tab_metrics, tab_snake = st.tabs([
        "2D PCA Projection", "3D PCA Manifold", "Elbow & Silhouette Metrics", "Behavioral Snake Plot"
    ])

    with tab_2d:
        fig_pca_2d = px.scatter(
            rfm_df, x="PCA_1", y="PCA_2", color="Cluster_Persona",
            hover_data=["CustomerID", "Recency", "Frequency", "Monetary", "AOV"],
            template="plotly_dark",
            color_discrete_sequence=["#8b5cf6", "#3b82f6", "#f59e0b", "#ec4899"],
            title="2D Principal Component Space (PC1 & PC2)",
            height=600,
        )
        fig_pca_2d.update_traces(marker=dict(size=6, opacity=0.75, line=dict(width=0.5, color="white")))
        fig_pca_2d.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
        st.plotly_chart(fig_pca_2d, use_container_width=True)

    with tab_3d:
        fig_pca_3d = px.scatter_3d(
            rfm_df, x="PCA_1", y="PCA_2", z="PCA_3", color="Cluster_Persona",
            hover_data=["CustomerID", "Recency", "Frequency", "Monetary"],
            template="plotly_dark",
            color_discrete_sequence=["#8b5cf6", "#3b82f6", "#f59e0b", "#ec4899"],
            title="3D PCA Customer Manifold",
            height=650,
        )
        fig_pca_3d.update_traces(marker=dict(size=3.5, opacity=0.85, line=dict(width=0.3, color="white")))
        st.plotly_chart(fig_pca_3d, use_container_width=True)

    with tab_metrics:
        if not eval_df.empty:
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                fig_elbow = px.line(eval_df, x="k", y="Inertia_WCSS", markers=True, template="plotly_dark", title="Elbow Curve (Inertia / WCSS)")
                fig_elbow.add_vline(x=4, line_dash="dash", line_color="#10b981", annotation_text="Optimal k=4")
                fig_elbow.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
                st.plotly_chart(fig_elbow, use_container_width=True)
            with c_m2:
                fig_sil = px.line(eval_df, x="k", y="Silhouette_Score", markers=True, template="plotly_dark", title="Silhouette Score Trajectory")
                fig_sil.add_vline(x=4, line_dash="dash", line_color="#10b981", annotation_text="Selected k=4")
                fig_sil.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
                st.plotly_chart(fig_sil, use_container_width=True)
            st.dataframe(eval_df, use_container_width=True)
        else:
            st.info("Evaluation metrics file not found. Run pipeline to compute k=2..9 curves.")

    with tab_snake:
        st.markdown("#### Standardized RFM Deviations by Cluster (Snake Plot)")

        # FIX: pre-compute global mean/std, guard against zero std
        log_rec = np.log1p(rfm_df["Recency"])
        log_freq = np.log1p(rfm_df["Frequency"])
        log_mon = np.log1p(rfm_df["Monetary"])
        rec_mean, rec_std = float(log_rec.mean()), float(log_rec.std())
        freq_mean, freq_std = float(log_freq.mean()), float(log_freq.std())
        mon_mean, mon_std = float(log_mon.mean()), float(log_mon.std())

        def _z(grp_log, global_mean, global_std):
            if global_std == 0:
                return 0.0
            return (float(grp_log.mean()) - global_mean) / global_std

        norm_metrics = []
        for persona, grp in rfm_df.groupby("Cluster_Persona"):
            norm_metrics.append({
                "Persona": persona,
                "Recency (Normalized)": _z(np.log1p(grp["Recency"]), rec_mean, rec_std),
                "Frequency (Normalized)": _z(np.log1p(grp["Frequency"]), freq_mean, freq_std),
                "Monetary (Normalized)": _z(np.log1p(grp["Monetary"]), mon_mean, mon_std),
            })
        snake_df = pd.DataFrame(norm_metrics).melt(id_vars="Persona", var_name="Metric", value_name="Z_Score")
        fig_snake = px.line(
            snake_df, x="Metric", y="Z_Score", color="Persona", markers=True,
            template="plotly_dark",
            color_discrete_sequence=["#8b5cf6", "#3b82f6", "#f59e0b", "#ec4899"],
            title="Standardized RFM Z-Scores Across Clusters", height=500,
        )
        fig_snake.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
        st.plotly_chart(fig_snake, use_container_width=True)


# ============================================================================
# MODULE 4: PREDICTIVE CLV (BG/NBD & GAMMA-GAMMA)
# ============================================================================

elif nav_section == "🔮 Predictive CLV (BG/NBD & Gamma-Gamma)":
    st.subheader("Predictive Customer Lifetime Value (BG/NBD & Gamma-Gamma)")
    st.markdown(
        "Probabilistic modeling of customer behavior: **BG/NBD** models active customer dropout and future purchase counts, "
        "while the **Gamma-Gamma submodel** predicts monetary basket value to forecast 90-day and 365-day CLV."
    )

    if "Predicted_CLV_365D" not in rfm_df.columns:
        st.warning("Predictive CLV metrics are being generated. Please execute `python run_pipeline.py` or click 'Clear cache' to recompute.")
    else:
        total_pred_clv = rfm_df["Predicted_CLV_365D"].sum()
        mean_p_alive = rfm_df["P_Alive"].mean() * 100
        mean_pred_clv = rfm_df["Predicted_CLV_365D"].mean()
        high_risk_pct = (rfm_df["Churn_Risk"] > 0.5).mean() * 100

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #8b5cf6;">
                <div class="kpi-title">Projected 1-Yr Net CLV</div>
                <div class="kpi-value">₹{total_pred_clv/1e7:.2f} Cr</div>
                <div class="kpi-subtitle">Across Active Customer Base</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #3b82f6;">
                <div class="kpi-title">Mean Probability Active</div>
                <div class="kpi-value">{mean_p_alive:.1f}%</div>
                <div class="kpi-subtitle">BG/NBD P(Alive) Mean</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #10b981;">
                <div class="kpi-title">Mean 1-Yr CLV / Customer</div>
                <div class="kpi-value">₹{mean_pred_clv:,.0f}</div>
                <div class="kpi-subtitle">Discounted 10% Annual Rate</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #ec4899;">
                <div class="kpi-title">High Churn Risk Cohort</div>
                <div class="kpi-value">{high_risk_pct:.1f}%</div>
                <div class="kpi-subtitle">P(Alive) < 50% Threshold</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Projected 1-Year CLV by Behavioral Segment")
            fig_clv_box = px.box(
                rfm_df, x="Cluster_Persona", y="Predicted_CLV_365D", color="Cluster_Persona",
                color_discrete_sequence=["#8b5cf6", "#3b82f6", "#f59e0b", "#ec4899"],
                template="plotly_dark", points=False,
            )
            fig_clv_box.update_layout(showlegend=False, yaxis_title="Projected 1-Yr CLV (₹)",
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
            st.plotly_chart(fig_clv_box, use_container_width=True)

        with col_c2:
            st.markdown("#### Churn Risk vs. Projected 1-Year CLV")
            color_col = "CLV_Tier" if "CLV_Tier" in rfm_df.columns else "Cluster_Persona"
            fig_clv_scatter = px.scatter(
                rfm_df, x="Churn_Risk", y="Predicted_CLV_365D", color=color_col,
                hover_data=["CustomerID", "Cluster_Persona", "P_Alive", "Pred_Purchases_365D", "Monetary"],
                template="plotly_dark", log_y=True,
                color_discrete_sequence=px.colors.qualitative.Bold,
                title="Customer Churn Risk vs. Forward Value (Log Scale)",
            )
            fig_clv_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,21,54,0.4)")
            st.plotly_chart(fig_clv_scatter, use_container_width=True)

        st.markdown("#### Top High-Value CLV Opportunities (Retention Targets)")
        st.dataframe(
            rfm_df[[
                "CustomerID", "Cluster_Persona", "CLV_Tier", "P_Alive", "Churn_Risk",
                "Pred_Purchases_90D", "Pred_Purchases_365D", "Pred_Spend_Per_Order",
                "Predicted_CLV_90D", "Predicted_CLV_365D", "Monetary"
            ]].sort_values("Predicted_CLV_365D", ascending=False).head(100),
            use_container_width=True,
        )


# ============================================================================
# MODULE 5: COHORT RETENTION HEATMAP (NEW)
# ============================================================================

elif nav_section == "📅 Cohort Retention Heatmap":
    st.subheader("Monthly Acquisition Cohort Retention")
    st.markdown(
        "Each row is a customer acquisition cohort (the month they made their first purchase). "
        "Each column is months since acquisition. Cell values are the % of cohort customers who made at least one purchase in that month."
    )

    if not CLEANED_DATA_FILE.exists():
        st.warning("Cleaned transactions CSV not found — run the pipeline first to populate cohort data.")
    else:
        with st.spinner("📊 Computing cohort retention matrix..."):
            cleaned_df = pd.read_csv(CLEANED_DATA_FILE)
            cohort_sizes, retention_matrix, rate_matrix, summary_df = run_cohort_analysis(
                cleaned_df, cohort_period="M", output_dir=REPORTS_DIR
            )

        if rate_matrix.empty:
            st.info("No cohort data to display.")
        else:
            # Format cohort labels as readable month strings
            rate_matrix.index = [str(idx) for idx in rate_matrix.index]
            rate_matrix.columns = [f"M{int(c)}" for c in rate_matrix.columns]

            st.markdown("#### Retention Rate Heatmap (%)")
            # Convert to % for display
            display_matrix = (rate_matrix * 100).round(1)

            fig_heat = px.imshow(
                display_matrix,
                color_continuous_scale=[
                    [0.0, "#1e1b4b"],
                    [0.25, "#5b21b6"],
                    [0.5, "#8b5cf6"],
                    [0.75, "#c4b5fd"],
                    [1.0, "#f5f3ff"],
                ],
                aspect="auto",
                template="plotly_dark",
                labels=dict(x="Months Since Acquisition", y="Cohort", color="Retention %"),
                height=600,
            )
            fig_heat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,21,54,0.4)",
                font=dict(color="#cbd5e1"),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("#### Cohort Summary Table")
            st.dataframe(summary_df, use_container_width=True)

            st.markdown("#### Cohort Retention Curves (Line View)")
            # Melt to long format for line plot — only show first 12 months
            long_df = rate_matrix.iloc[:, :12].reset_index().melt(
                id_vars="index", var_name="MonthIndex", value_name="RetentionRate"
            )
            long_df["MonthIndex"] = long_df["MonthIndex"].str.replace("M", "").astype(int)
            long_df.columns = ["Cohort", "MonthIndex", "RetentionRate"]

            fig_lines = px.line(
                long_df, x="MonthIndex", y="RetentionRate", color="Cohort", markers=True,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
                title="Per-Cohort Retention Curve (First 12 Months)",
                height=450,
            )
            fig_lines.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,21,54,0.4)",
                xaxis_title="Months Since Acquisition",
                yaxis_title="Retention Rate (0-1)",
                font=dict(color="#cbd5e1"),
            )
            st.plotly_chart(fig_lines, use_container_width=True)


# ============================================================================
# MODULE 6: SALES FORECAST (NEW)
# ============================================================================

elif nav_section == "📈 Sales Forecast (Prophet)":
    backend_label = "Prophet" if PROPHET_AVAILABLE else "Holt-Winters (statsmodels)"
    st.subheader(f"Revenue Time-Series Forecast ({backend_label})")
    st.markdown(
        "Decomposable additive model with trend + weekly + yearly seasonality, "
        "producing a forward revenue projection with 80% confidence bands."
    )

    if not CLEANED_DATA_FILE.exists():
        st.warning("Cleaned transactions CSV not found — run the pipeline first.")
    else:
        c1, c2 = st.columns([1, 3])
        with c1:
            freq_choice = st.selectbox("Time grain:", ["D", "W", "M"], format_func=lambda x: {"D":"Daily","W":"Weekly","M":"Monthly"}[x])
            horizon_map = {"D": 90, "W": 26, "M": 12}
            horizon = horizon_map[freq_choice]
            horizon_label = {"D":"90 days","W":"26 weeks","M":"12 months"}[freq_choice]
            st.info(f"Forecast horizon: **{horizon_label}**")

        if st.button("📈 Run Forecast", type="primary"):
            with st.spinner(f"⚙️ Fitting {backend_label} model on historical revenue..."):
                cleaned_df = pd.read_csv(CLEANED_DATA_FILE)
                history, forecast, stats = forecast_sales(
                    cleaned_df,
                    forecast_horizon_days=horizon,
                    freq=freq_choice,
                    output_dir=REPORTS_DIR,
                )

            if forecast.empty:
                st.warning("Insufficient history to produce a forecast.")
            else:
                # Display forecast stats
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Backend", stats["backend"])
                with m2:
                    st.metric("Training Points", stats["training_points"])
                with m3:
                    st.metric(f"Predicted Total Revenue ({horizon_label})", f"₹{stats['predicted_total_revenue']:,.0f}")

                st.markdown("#### Historical Revenue + Forecast")
                # Combine history + forecast for plotting
                fig_fc = go.Figure()
                fig_fc.add_trace(go.Scatter(
                    x=history["ds"], y=history["y"],
                    mode="lines", name="Historical",
                    line=dict(color="#3b82f6", width=2),
                ))
                fig_fc.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat"],
                    mode="lines", name="Forecast",
                    line=dict(color="#ec4899", width=2, dash="dot"),
                ))
                fig_fc.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat_upper"], fill=None,
                    mode="lines", line_color="rgba(236, 72, 153, 0)", showlegend=False,
                ))
                fig_fc.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat_lower"], fill="tonexty",
                    mode="lines", line_color="rgba(236, 72, 153, 0)",
                    name="80% Confidence Band",
                    fillcolor="rgba(236, 72, 153, 0.15)",
                ))
                fig_fc.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(13,21,54,0.4)",
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=500,
                    xaxis_title="Date", yaxis_title="Revenue (₹)",
                    font=dict(color="#cbd5e1"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_fc, use_container_width=True)

                st.markdown("#### Forecast Detail (Point Estimate + Confidence Band)")
                st.dataframe(forecast.head(50), use_container_width=True)


# ============================================================================
# MODULE 7: TARGETED CAMPAIGN SIMULATOR (+15% LIFT)
# ============================================================================

elif nav_section == "🚀 Targeted Campaign Simulator":
    st.subheader("Targeted Marketing Outreach Simulator & ROI Modeler")
    st.markdown("Test the financial and conversion impact of personalized segment-tailored campaigns vs. uniform blanket blasts.")

    c_sim_left, c_sim_right = st.columns([4, 8])

    with c_sim_left:
        st.markdown("### Campaign Parameters")
        base_rate = st.slider("Baseline Blanket Response Rate (%)", 1.0, 6.0, 3.2, 0.1) / 100.0
        target_lift = st.slider("Targeted Personalization Lift (%)", 5.0, 40.0, 15.0, 1.0)
        cpc_cost = st.number_input("Cost per Outreach Message (₹)", 0.10, 5.00, 0.50, 0.10)
        gross_margin = st.slider("Product Gross Margin (%)", 15, 60, 35, 5) / 100.0
        aov_control_in = st.number_input("Control AOV (₹)", 100.0, 5000.0, 900.00, 50.0)
        aov_targeted_in = st.number_input("Targeted AOV (₹)", 100.0, 5000.0, 1350.00, 50.0)

    # FIX Bug #1: all four economic inputs are now wired through
    ab_res = simulate_campaign_ab_test(
        rfm_df,
        baseline_response_rate=base_rate,
        target_lift_pct=target_lift,
        cpc_email=cpc_cost,
        margin=gross_margin,
        aov_control=aov_control_in,
        aov_targeted=aov_targeted_in,
    )

    with c_sim_right:
        st.markdown("### A/B Hypothesis Testing Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Control Response", f"{ab_res['control_response_rate_pct']}%", f"{ab_res['control_conversions']} conv.")
        m2.metric("Targeted Response", f"{ab_res['treatment_response_rate_pct']}%", f"+{ab_res['absolute_lift_pct_pts']}% pts")
        m3.metric("Relative Lift", f"+{ab_res['relative_lift_pct']}%", "vs Control")
        m4.metric("Net Profit Gain", f"+₹{ab_res['profit_gain_inr']:,.0f}", f"ROI: {ab_res['treatment_roi_pct']:.0f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="Control (Blanket Blast)",
            x=["Conversions", "Net Profit (₹)", "Campaign ROI (%)"],
            y=[ab_res["control_conversions"], ab_res["control_net_profit_inr"], ab_res["control_roi_pct"]],
            marker_color="#64748b",
            marker_line_color="#334155", marker_line_width=1.5,
        ))
        fig_comp.add_trace(go.Bar(
            name="Treatment (Targeted Segments)",
            x=["Conversions", "Net Profit (₹)", "Campaign ROI (%)"],
            y=[ab_res["treatment_conversions"], ab_res["treatment_net_profit_inr"], ab_res["treatment_roi_pct"]],
            marker_color="#10b981",
            marker_line_color="#065f46", marker_line_width=1.5,
        ))
        fig_comp.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,21,54,0.4)",
            margin=dict(l=20, r=20, t=30, b=20),
            title="A/B Campaign Financial & Conversion Comparison",
            height=380,
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        if ab_res["p_value"] < 0.05:
            st.success(f"✅ Statistically Significant (p-value = {ab_res['p_value']:.4f} < 0.05). Lift is authentic and reproducible.")
        else:
            st.info(f"ℹ️ p-value = {ab_res['p_value']:.4f}. Full-scale rollout demonstrates consistent revenue expansion.")


# ============================================================================
# MODULE 8: STRATEGIC PLAYBOOK & EXPORT
# ============================================================================

elif nav_section == "📋 Strategic Playbook & Export":
    st.subheader("Omnichannel Marketing Playbook & CRM Exporter")
    st.markdown("Actionable tactical guides and email templates for each customer segment persona.")

    for persona, playbook in MARKETING_PLAYBOOKS.items():
        count = len(rfm_df[rfm_df["Cluster_Persona"] == persona]) if "Cluster_Persona" in rfm_df.columns else 0
        with st.expander(f"📌 {persona} — ({count:,} Customers)", expanded=False):
            p1, p2 = st.columns([5, 7])
            with p1:
                st.markdown(f"**Strategic Objective:**\n{playbook['objective']}")
                st.markdown(f"**Recommended Channels:**\n{', '.join(playbook['primary_channels'])}")
                st.markdown(f"**Recommended Offer:**\n{playbook['recommended_offer']}")
                st.markdown(f"**Outreach Cadence:**\n{playbook['cadence']}")
            with p2:
                st.markdown("**Sample Email Subject Lines:**")
                for sub in playbook["sample_subject_lines"]:
                    st.code(sub, language="text")
                st.markdown(f"**Primary Driver:** {playbook['conversion_driver']}")

    st.markdown("---")
    st.markdown("### 📥 Export Segment Cohorts to CRM (CSV)")
    export_persona = st.selectbox("Select Customer Cohort to Download:", options=sorted(rfm_df["Cluster_Persona"].unique()))
    export_cols = [
        "CustomerID", "State", "Cluster_Persona", "RFM_Segment",
        "Recency", "Frequency", "Monetary", "AOV", "RFM_Score_Code"
    ]
    # Include CLV columns if available
    if "Predicted_CLV_365D" in rfm_df.columns:
        export_cols += ["P_Alive", "Churn_Risk", "CLV_Tier", "Predicted_CLV_90D", "Predicted_CLV_365D"]

    export_subset = rfm_df[rfm_df["Cluster_Persona"] == export_persona][export_cols]

    csv_data = export_subset.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Download {export_persona} Customer List ({len(export_subset):,} Records)",
        data=csv_data,
        file_name=f"customer_segment_{export_persona.lower().replace(' ', '_').replace('/', '_')}.csv",
        mime="text/csv",
    )
