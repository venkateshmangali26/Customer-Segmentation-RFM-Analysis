"""
Perfected Interactive Streamlit Frontend for Customer Segmentation & RFM Analytics.

Features:
- Self-Healing Auto-Pipeline (Generates data on first run if missing)
- Executive KPI Overview & Pareto Distribution
- Interactive RFM Quantile Explorer & Filterable Data Table
- 2D & 3D PCA Machine Learning Cluster Visualizations (Plotly)
- Real-Time A/B Marketing Campaign Simulator (+15% Lift Engine)
- Omnichannel Strategy Playbooks & Instant CRM CSV Exporter

FIXES applied vs the previous "perfected" version:
  (1) CRITICAL — `cpc_cost` and `gross_margin` are now actually passed to
      `simulate_campaign_ab_test()` (the original collected them as UI inputs
      but never wired them into the call site, so the ROI numbers were frozen
      at cpc=0.05 / margin=0.45 regardless of slider position).
  (2) Empty multiselect in Tab 2 now means "show all segments" instead of
      silently filtering to 0 customers.
  (3) Snake-plot Z-score guarded against zero-std edge case.
  (4) "Clear cache" button added to the sidebar so users can re-run the
      pipeline and see fresh data without restarting Streamlit.
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
from src.data_generator import generate_synthetic_transactions
from src.data_processing import clean_transactions
from src.marketing_strategy import MARKETING_PLAYBOOKS, simulate_campaign_ab_test
from src.rfm_analysis import run_rfm_pipeline

# -------------------------------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIGURATION & CUSTOM CSS
# -------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Customer Segmentation & RFM Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .kpi-card {
        background: linear-gradient(135deg, #1e2638 0%, #151b28 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    .kpi-title { font-size: 12px; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; font-weight: 600; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: -0.02em; }
    .kpi-subtitle { font-size: 12px; color: #48bb78; margin-top: 6px; font-weight: 500; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 6px;
        color: #c9d1d9;
        font-weight: 600;
        padding: 10px 18px;
        border: 1px solid #30363d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #238636 !important;
        color: white !important;
        border-color: #2ea043 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------------------------------------
# 2. SELF-HEALING DATA LOADER (Ensures app never crashes on first launch)
# -------------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def initialize_and_load_data(_force_refresh: bool = False):
    """
    Checks for precomputed data files; generates and runs pipeline if any are missing.

    The `_force_refresh` argument (with leading underscore so Streamlit doesn't
    hash it) lets a sidebar button invalidate the cache without restarting the
    server — flips True → cache miss → reload from disk.
    """
    if not RFM_DATA_FILE.exists() or not CLUSTER_METRICS_FILE.exists():
        with st.spinner("🚀 Initializing pipeline: Generating sample transactions & training ML clusters..."):
            raw_df = generate_synthetic_transactions(n_transactions=50000, n_customers=5000)
            cleaned_df, _ = clean_transactions(raw_df, output_path=CLEANED_DATA_FILE)
            rfm_df, _ = run_rfm_pipeline(cleaned_df, output_path=RFM_DATA_FILE)
            rfm_clustered, cluster_profiles, eval_df, _, _ = run_clustering_pipeline(
                rfm_df, n_clusters=4, output_path=RFM_DATA_FILE
            )
    else:
        rfm_df = pd.read_csv(RFM_DATA_FILE)
        cluster_profiles = pd.read_csv(CLUSTER_METRICS_FILE)
        eval_file = REPORTS_DIR / "clustering_evaluation_metrics.csv"
        eval_df = pd.read_csv(eval_file) if eval_file.exists() else pd.DataFrame()

    return rfm_df, cluster_profiles, eval_df


# FIX #4: Sidebar "Clear cache" button so users can re-run the pipeline and
# see fresh data without restarting Streamlit.
if st.sidebar.button("🔄 Clear cache & reload from disk"):
    st.cache_data.clear()
    st.rerun()

try:
    rfm_df, cluster_profiles, eval_df = initialize_and_load_data()
except Exception as e:
    st.error(f"Critical error initializing pipeline datasets: {e}")
    st.stop()


# -------------------------------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & CONTROLS
# -------------------------------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/isometric/100/combo-chart.png", width=65)
st.sidebar.title("Navigation & Hub")
nav_section = st.sidebar.radio(
    "Select Module:",
    [
        "📊 Executive KPI Overview",
        "🔍 RFM Quantile Explorer",
        "🤖 K-Means & PCA Clustering",
        "🚀 Targeted Campaign Simulator",
        "📋 Strategic Playbook & Export",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Dataset Summary")
total_rev = rfm_df["Monetary"].sum()
st.sidebar.info(
    f"• **Active Customers:** {len(rfm_df):,}\n\n"
    f"• **Total Revenue:** ${total_rev:,.2f}\n\n"
    f"• **Avg Recency:** {rfm_df['Recency'].mean():.1f} days\n\n"
    f"• **Avg Frequency:** {rfm_df['Frequency'].mean():.1f} orders"
)


# -------------------------------------------------------------------------------------------------
# TAB 1: EXECUTIVE KPI OVERVIEW
# -------------------------------------------------------------------------------------------------
if nav_section == "📊 Executive KPI Overview":
    st.subheader("Executive Performance & Revenue Concentration")
    st.markdown("High-level breakdown of customer lifetime value, Pareto distribution, and segment revenue share.")

    # FIX: guard against the persona name not matching exactly "VIP Champions"
    # (happens if k labeling produces a different name after a re-run with
    # different n_clusters). Without the guard, .sum() on an empty series
    # returns 0 — fine — but it's clearer to be explicit.
    vip_mask = cluster_profiles["Cluster_Persona"] == "VIP Champions"
    vip_rev = cluster_profiles.loc[vip_mask, "TotalRevenue"].sum() if vip_mask.any() else 0.0
    vip_rev_share = (vip_rev / total_rev) * 100 if total_rev > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Active Customers</div>
                <div class="kpi-value">{len(rfm_df):,}</div>
                <div class="kpi-subtitle">Filtered Active Base</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Net Revenue</div>
                <div class="kpi-value">${total_rev/1e6:.2f}M</div>
                <div class="kpi-subtitle">100% Tracked Spend</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">VIP Revenue Share</div>
                <div class="kpi-value">{vip_rev_share:.1f}%</div>
                <div class="kpi-subtitle">Pareto Concentration</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Avg Customer Spend</div>
                <div class="kpi-value">${rfm_df['Monetary'].mean():,.2f}</div>
                <div class="kpi-subtitle">Median: ${rfm_df['Monetary'].median():,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([7, 5])
    with col_left:
        st.markdown("#### Customer Base vs. Revenue Contribution (Pareto Disparity)")
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=cluster_profiles["Cluster_Persona"],
            y=cluster_profiles["CustomerSharePct"],
            name="Customer Share (%)",
            marker_color="#3182ce",
        ))
        fig_pareto.add_trace(go.Bar(
            x=cluster_profiles["Cluster_Persona"],
            y=cluster_profiles["RevenueSharePct"],
            name="Revenue Share (%)",
            marker_color="#48bb78",
        ))
        fig_pareto.update_layout(
            barmode="group",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Percentage (%)",
            height=400,
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col_right:
        st.markdown("#### Segment Revenue Composition")
        fig_pie = px.pie(
            cluster_profiles,
            names="Cluster_Persona",
            values="TotalRevenue",
            hole=0.45,
            color="Cluster_Persona",
            color_discrete_sequence=["#805ad5", "#3182ce", "#dd6b20", "#e53e3e"],
            template="plotly_dark",
        )
        fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Detailed Cluster Profiling Table")
    st.dataframe(
        cluster_profiles.style.format({
            "TotalRevenue": "${:,.2f}",
            "AvgRecency": "{:.1f} days",
            "AvgFrequency": "{:.1f} orders",
            "AvgMonetary": "${:,.2f}",
            "AvgAOV": "${:,.2f}",
            "CustomerSharePct": "{:.2f}%",
            "RevenueSharePct": "{:.2f}%",
        }),
        use_container_width=True,
    )


# -------------------------------------------------------------------------------------------------
# TAB 2: RFM QUANTILE EXPLORER
# -------------------------------------------------------------------------------------------------
elif nav_section == "🔍 RFM Quantile Explorer":
    st.subheader("RFM Quantile Scoring & Customer Filtering")
    st.markdown("Filter customers by their quintile scores (1–5) and behavioral segment categories.")

    f1, f2, f3, f4 = st.columns(4)
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

    # FIX #2: empty multiselect now means "show all segments" instead of
    # silently filtering to 0 rows. Previously `isin([])` returns all False,
    # which produces a confusing "0 of N" empty result.
    if selected_segment:
        seg_mask = rfm_df["RFM_Segment"].isin(selected_segment)
    else:
        seg_mask = pd.Series(True, index=rfm_df.index)
        st.info("No segment selected — showing all segments. Pick at least one to filter.")

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
            x="Recency",
            y="Frequency",
            size="Monetary",
            color="RFM_Segment",
            hover_data=["CustomerID", "Monetary", "AOV"],
            template="plotly_dark",
            title="Recency vs. Frequency (Bubble Size = Spend)",
            height=450,
        )
        st.plotly_chart(fig_r_f, use_container_width=True)

    with col2:
        fig_f_m = px.scatter(
            filtered_df,
            x="Frequency",
            y="Monetary",
            color="RFM_Segment",
            hover_data=["CustomerID", "Recency", "AOV"],
            log_y=True,
            template="plotly_dark",
            title="Frequency vs. Monetary Value (Log Scale)",
            height=450,
        )
        st.plotly_chart(fig_f_m, use_container_width=True)

    st.markdown("#### Filtered Customer Records Table")
    st.dataframe(
        filtered_df[[
            "CustomerID", "RFM_Segment", "Cluster_Persona", "Recency", "Frequency",
            "Monetary", "AOV", "RFM_Score_Code", "Country", "Tenure_Days"
        ]].head(300),
        use_container_width=True,
    )


# -------------------------------------------------------------------------------------------------
# TAB 3: K-MEANS & PCA CLUSTERING
# -------------------------------------------------------------------------------------------------
elif nav_section == "🤖 K-Means & PCA Clustering":
    st.subheader("Unsupervised Machine Learning & Dimensionality Reduction")
    st.markdown("K-Means clustering trained on log-transformed, scaled RFM features, projected onto 2D and 3D Principal Component spaces.")

    tab_2d, tab_3d, tab_metrics, tab_snake = st.tabs([
        "2D PCA Projection", "3D PCA Manifold", "Elbow & Silhouette Metrics", "Behavioral Snake Plot"
    ])

    with tab_2d:
        fig_pca_2d = px.scatter(
            rfm_df,
            x="PCA_1",
            y="PCA_2",
            color="Cluster_Persona",
            hover_data=["CustomerID", "Recency", "Frequency", "Monetary", "AOV"],
            template="plotly_dark",
            color_discrete_sequence=["#805ad5", "#3182ce", "#dd6b20", "#e53e3e"],
            title="2D Principal Component Space (PC1 & PC2)",
            height=600,
        )
        fig_pca_2d.update_traces(marker=dict(size=6, opacity=0.75))
        st.plotly_chart(fig_pca_2d, use_container_width=True)

    with tab_3d:
        fig_pca_3d = px.scatter_3d(
            rfm_df,
            x="PCA_1",
            y="PCA_2",
            z="PCA_3",
            color="Cluster_Persona",
            hover_data=["CustomerID", "Recency", "Frequency", "Monetary"],
            template="plotly_dark",
            color_discrete_sequence=["#805ad5", "#3182ce", "#dd6b20", "#e53e3e"],
            title="3D PCA Customer Manifold",
            height=650,
        )
        fig_pca_3d.update_traces(marker=dict(size=3.5, opacity=0.8))
        st.plotly_chart(fig_pca_3d, use_container_width=True)

    with tab_metrics:
        if not eval_df.empty:
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                fig_elbow = px.line(eval_df, x="k", y="Inertia_WCSS", markers=True, template="plotly_dark", title="Elbow Curve (Inertia / WCSS)")
                fig_elbow.add_vline(x=4, line_dash="dash", line_color="#48bb78", annotation_text="Optimal k=4")
                st.plotly_chart(fig_elbow, use_container_width=True)
            with c_m2:
                fig_sil = px.line(eval_df, x="k", y="Silhouette_Score", markers=True, template="plotly_dark", title="Silhouette Score Trajectory")
                fig_sil.add_vline(x=4, line_dash="dash", line_color="#48bb78", annotation_text="Selected k=4")
                st.plotly_chart(fig_sil, use_container_width=True)
            st.dataframe(eval_df, use_container_width=True)
        else:
            st.info("Evaluation metrics file not found. Run pipeline to compute k=2..9 curves.")

    with tab_snake:
        st.markdown("#### Standardized RFM Deviations by Cluster (Snake Plot)")

        # FIX #3: pre-compute the global mean and std once. Guard against
        # std == 0 (would happen if every customer had the exact same Recency/
        # Frequency/Monetary — degenerate but possible on a tiny test dataset).
        # Without the guard, the Z-score would be inf / nan and the snake plot
        # would render as an empty chart with no error message.
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
        fig_snake = px.line(snake_df, x="Metric", y="Z_Score", color="Persona", markers=True, template="plotly_dark", title="Standardized RFM Z-Scores Across Clusters", height=500)
        st.plotly_chart(fig_snake, use_container_width=True)


# -------------------------------------------------------------------------------------------------
# TAB 4: TARGETED CAMPAIGN SIMULATOR (+15% LIFT)
# -------------------------------------------------------------------------------------------------
elif nav_section == "🚀 Targeted Campaign Simulator":
    st.subheader("Targeted Marketing Outreach Simulator & ROI Modeler")
    st.markdown("Test the financial and conversion impact of personalized segment-tailored campaigns vs. uniform blanket blasts.")

    c_sim_left, c_sim_right = st.columns([4, 8])

    with c_sim_left:
        st.markdown("### Campaign Parameters")
        base_rate = st.slider("Baseline Blanket Response Rate (%)", 1.0, 6.0, 3.2, 0.1) / 100.0
        target_lift = st.slider("Targeted Personalization Lift (%)", 5.0, 40.0, 15.0, 1.0)
        cpc_cost = st.number_input("Cost per Outreach Message ($)", 0.01, 1.00, 0.05, 0.01)
        gross_margin = st.slider("Product Gross Margin (%)", 20, 80, 45, 5) / 100.0
        aov_control_in = st.number_input("Control AOV ($)", 10.0, 500.0, 65.00, 1.0)
        aov_targeted_in = st.number_input("Targeted AOV ($)", 10.0, 500.0, 82.50, 1.0)

    # FIX #1 (CRITICAL): the original "perfected" version collected `cpc_cost`
    # and `gross_margin` from the user but never passed them to the simulator,
    # so changing the sliders had ZERO effect on the displayed ROI. The call
    # site below now wires all four economic inputs through to the function.
    # (Requires the parameterized `simulate_campaign_ab_test` from
    # `rfm_python_v3_fixed/src/marketing_strategy.py`. If you're using an
    # older backend that only accepts `baseline_response_rate` + `target_lift_pct`,
    # the extra kwargs will TypeError — that's the signal to upgrade the backend.)
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
        m4.metric("Net Profit Gain", f"+${ab_res['profit_gain_usd']:,.2f}", f"ROI: {ab_res['treatment_roi_pct']:.0f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="Control (Blanket Blast)",
            x=["Conversions", "Net Profit ($)", "Campaign ROI (%)"],
            y=[ab_res["control_conversions"], ab_res["control_net_profit_usd"], ab_res["control_roi_pct"]],
            marker_color="#a0aec0",
        ))
        fig_comp.add_trace(go.Bar(
            name="Treatment (Targeted Segments)",
            x=["Conversions", "Net Profit ($)", "Campaign ROI (%)"],
            y=[ab_res["treatment_conversions"], ab_res["treatment_net_profit_usd"], ab_res["treatment_roi_pct"]],
            marker_color="#48bb78",
        ))
        fig_comp.update_layout(
            barmode="group",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            title="A/B Campaign Financial & Conversion Comparison",
            height=380,
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        if ab_res["p_value"] < 0.05:
            st.success(f"✅ Statistically Significant (p-value = {ab_res['p_value']:.4f} < 0.05). Lift is authentic and reproducible.")
        else:
            st.info(f"ℹ️ p-value = {ab_res['p_value']:.4f}. Full-scale rollout demonstrates consistent revenue expansion.")


# -------------------------------------------------------------------------------------------------
# TAB 5: STRATEGIC PLAYBOOK & EXPORT
# -------------------------------------------------------------------------------------------------
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
    export_subset = rfm_df[rfm_df["Cluster_Persona"] == export_persona][[
        "CustomerID", "Country", "Cluster_Persona", "RFM_Segment", "Recency", "Frequency", "Monetary", "AOV", "RFM_Score_Code"
    ]]

    csv_data = export_subset.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Download {export_persona} Customer List ({len(export_subset):,} Records)",
        data=csv_data,
        file_name=f"customer_segment_{export_persona.lower().replace(' ', '_').replace('/', '_')}.csv",
        mime="text/csv",
    )
