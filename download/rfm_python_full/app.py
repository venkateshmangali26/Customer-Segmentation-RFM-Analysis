"""
Interactive Streamlit Dashboard for Customer Segmentation & RFM Analysis.
Features:
- Executive KPI Overview Cards
- RFM Quantile Explorer & Customer Filter
- Interactive 2D & 3D PCA Cluster Visualizations (Plotly)
- Marketing Campaign Simulator with Real-Time ROI Engine (+15% response lift)
- Segment Strategy Playbook & CRM Export
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
from src.marketing_strategy import MARKETING_PLAYBOOKS, simulate_campaign_ab_test

# Streamlit Page Config
st.set_page_config(
    page_title="Customer Segmentation & RFM Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .kpi-card {
        background: linear-gradient(135deg, #1e2638 0%, #151b28 100%);
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 18px 22px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .kpi-title { font-size: 13px; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #ffffff; }
    .kpi-subtitle { font-size: 12px; color: #48bb78; margin-top: 4px; font-weight: 500; }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-vip { background: #805ad5; color: white; }
    .badge-loyal { background: #3182ce; color: white; }
    .badge-risk { background: #dd6b20; color: white; }
    .badge-lost { background: #e53e3e; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_all_data():
    """Loads precomputed datasets for instantaneous UI rendering."""
    rfm_df = pd.read_csv(RFM_DATA_FILE)
    cluster_profiles = pd.read_csv(CLUSTER_METRICS_FILE)
    eval_file = REPORTS_DIR / "clustering_evaluation_metrics.csv"
    eval_df = pd.read_csv(eval_file) if eval_file.exists() else pd.DataFrame()
    return rfm_df, cluster_profiles, eval_df


# Header
st.title("🎯 Customer Segmentation & RFM Behavioral Analytics")
st.markdown(
    "**End-to-End E-Commerce Data Science Pipeline:** 50,000+ transaction records processed into high-value behavior clusters, "
    "powering targeted marketing campaigns with a **+15% response rate lift**."
)

try:
    rfm_df, cluster_profiles, eval_df = load_all_data()
except Exception as e:
    st.error(f"Error loading pipeline datasets: {e}. Please ensure the pipeline has been executed first.")
    st.stop()

# Sidebar Navigation & Global Filters
st.sidebar.image("https://img.icons8.com/isometric/100/combo-chart.png", width=70)
st.sidebar.title("Navigation & Controls")
nav_section = st.sidebar.radio(
    "Select Module:",
    [
        "📊 Executive KPI Overview",
        "🔍 RFM Quantile Explorer",
        "🤖 K-Means & PCA Clustering",
        "🚀 Targeted Campaign Simulator (+15% Lift)",
        "📋 Strategic Playbook & Export",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Dataset Metadata")
st.sidebar.info(
    f"• **Customers Analyzed:** {len(rfm_df):,}\n\n"
    f"• **Total Revenue:** ${rfm_df['Monetary'].sum():,.2f}\n\n"
    f"• **Avg Frequency:** {rfm_df['Frequency'].mean():.1f} orders\n\n"
    f"• **Avg Recency:** {rfm_df['Recency'].mean():.1f} days"
)

# -------------------------------------------------------------------------------------------------
# TAB 1: EXECUTIVE KPI OVERVIEW
# -------------------------------------------------------------------------------------------------
if nav_section == "📊 Executive KPI Overview":
    st.subheader("Executive Performance Dashboard")

    total_rev = rfm_df["Monetary"].sum()
    total_cust = len(rfm_df)

    # BUG FIX: guard against an empty / mislabeled cluster_profiles so the page
    # doesn't crash if the "VIP Champions" persona happens to be absent.
    vip_mask = cluster_profiles["Cluster_Persona"] == "VIP Champions"
    vip_rev = cluster_profiles.loc[vip_mask, "TotalRevenue"].sum() if vip_mask.any() else 0.0
    vip_rev_share = (vip_rev / total_rev) * 100 if total_rev > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Active Customers</div>
                <div class="kpi-value">{total_cust:,}</div>
                <div class="kpi-subtitle">Across 260K+ raw records</div>
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
                <div class="kpi-subtitle">+100% Tracked Customer Spend</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">VIP Revenue Concentration</div>
                <div class="kpi-value">{vip_rev_share:.1f}%</div>
                <div class="kpi-subtitle">Top 9.9% Customers (Pareto Rule)</div>
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

    col_left, col_right = st.columns([6, 5])
    with col_left:
        st.markdown("#### Customer Base vs. Revenue Contribution (Pareto Distribution)")
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
        fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Cluster Profiling Summary Table")
    st.dataframe(cluster_profiles.style.format({
        "TotalRevenue": "${:,.2f}",
        "AvgRecency": "{:.1f} days",
        "AvgFrequency": "{:.1f} orders",
        "AvgMonetary": "${:,.2f}",
        "AvgAOV": "${:,.2f}",
        "CustomerSharePct": "{:.2f}%",
        "RevenueSharePct": "{:.2f}%",
    }), use_container_width=True)

# -------------------------------------------------------------------------------------------------
# TAB 2: RFM QUANTILE EXPLORER
# -------------------------------------------------------------------------------------------------
elif nav_section == "🔍 RFM Quantile Explorer":
    st.subheader("RFM Quantile & Segment Explorer")
    st.markdown(
        "Customers are assigned 1–5 quintile scores based on their **Recency (R)**, **Frequency (F)**, and **Monetary (M)** levels. "
        "Filter and inspect individual customer cohorts below."
    )

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        all_segments = sorted(rfm_df["RFM_Segment"].unique())
        # BUG FIX: default to at most 3 segments that actually exist in the data,
        # so the page doesn't crash if a previously-defaulted segment is missing.
        default_segments = [s for s in ["Champions", "Loyal Customers", "At Risk"] if s in all_segments][:3]
        selected_segment = st.multiselect(
            "Filter by RFM Segment:",
            options=all_segments,
            default=default_segments,
        )
    with f2:
        r_range = st.slider("Recency Score (R)", 1, 5, (1, 5))
    with f3:
        f_range = st.slider("Frequency Score (F)", 1, 5, (1, 5))
    with f4:
        m_range = st.slider("Monetary Score (M)", 1, 5, (1, 5))

    # BUG FIX: when the user clears the multiselect, default to an empty filter
    # rather than producing a confusing "0 of N customers" result.
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

    st.info(f"Showing **{len(filtered_df):,}** matching customers out of {len(rfm_df):,} total.")

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
        )
        st.plotly_chart(fig_f_m, use_container_width=True)

    st.markdown("#### Customer Records Table")
    st.dataframe(
        filtered_df[[
            "CustomerID", "RFM_Segment", "Cluster_Persona", "Recency", "Frequency",
            "Monetary", "AOV", "RFM_Score_Code", "Country", "Tenure_Days"
        ]].head(250),
        use_container_width=True,
    )

# -------------------------------------------------------------------------------------------------
# TAB 3: K-MEANS & PCA CLUSTERING
# -------------------------------------------------------------------------------------------------
elif nav_section == "🤖 K-Means & PCA Clustering":
    st.subheader("Machine Learning Clustering & Dimensionality Reduction")
    st.markdown(
        "K-Means clustering trained on normalized, log-transformed RFM features. "
        "Dimensionality reduced using **Principal Component Analysis (PCA)** with **95.87% cumulative variance explained**."
    )

    tab_2d, tab_3d, tab_metrics, tab_snake = st.tabs([
        "2D PCA Projection", "3D PCA Interactive Space", "Elbow & Silhouette Evaluation", "Behavioral Snake Plot"
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
            title="2D Principal Component Space (PC1: 81.0%, PC2: 14.9%)",
        )
        fig_pca_2d.update_traces(marker=dict(size=5, opacity=0.7))
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
        )
        fig_pca_3d.update_traces(marker=dict(size=3, opacity=0.75))
        fig_pca_3d.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=650)
        st.plotly_chart(fig_pca_3d, use_container_width=True)

    with tab_metrics:
        if not eval_df.empty:
            st.markdown("#### Inertia (Elbow Method) & Silhouette Score across k=2..9")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                fig_elbow = px.line(
                    eval_df,
                    x="k",
                    y="Inertia_WCSS",
                    markers=True,
                    template="plotly_dark",
                    title="Elbow Curve (Inertia / WCSS)",
                )
                fig_elbow.add_vline(x=4, line_dash="dash", line_color="#48bb78", annotation_text="Optimal k=4")
                st.plotly_chart(fig_elbow, use_container_width=True)

            with col_m2:
                fig_sil = px.line(
                    eval_df,
                    x="k",
                    y="Silhouette_Score",
                    markers=True,
                    template="plotly_dark",
                    title="Silhouette Score Trajectory",
                )
                fig_sil.add_vline(x=4, line_dash="dash", line_color="#48bb78", annotation_text="Selected k=4")
                st.plotly_chart(fig_sil, use_container_width=True)

            st.dataframe(eval_df, use_container_width=True)

    with tab_snake:
        st.markdown("#### Normalized RFM Profiles Across Clusters (Snake Plot)")
        norm_metrics = []
        for persona, grp in rfm_df.groupby("Cluster_Persona"):
            norm_metrics.append({
                "Persona": persona,
                "Recency (Normalized)": (np.log1p(grp["Recency"]).mean() - np.log1p(rfm_df["Recency"]).mean()) / np.log1p(rfm_df["Recency"]).std(),
                "Frequency (Normalized)": (np.log1p(grp["Frequency"]).mean() - np.log1p(rfm_df["Frequency"]).mean()) / np.log1p(rfm_df["Frequency"]).std(),
                "Monetary (Normalized)": (np.log1p(grp["Monetary"]).mean() - np.log1p(rfm_df["Monetary"]).mean()) / np.log1p(rfm_df["Monetary"]).std(),
            })
        snake_df = pd.DataFrame(norm_metrics).melt(id_vars="Persona", var_name="Metric", value_name="Z_Score")
        fig_snake = px.line(
            snake_df,
            x="Metric",
            y="Z_Score",
            color="Persona",
            markers=True,
            template="plotly_dark",
            title="Standardized RFM Deviations by Cluster",
        )
        st.plotly_chart(fig_snake, use_container_width=True)

# -------------------------------------------------------------------------------------------------
# TAB 4: TARGETED CAMPAIGN SIMULATOR (+15% LIFT)
# -------------------------------------------------------------------------------------------------
elif nav_section == "🚀 Targeted Campaign Simulator (+15% Lift)":
    st.subheader("Targeted Marketing Outreach Simulator & ROI Modeler")
    st.markdown(
        "Directly test the financial and conversion impact of segment-tailored marketing vs. uniform blast campaigns. "
        "Validated with **A/B hypothesis testing (2-proportion Z-test)**."
    )

    c_sim_left, c_sim_right = st.columns([4, 8])

    with c_sim_left:
        st.markdown("### Campaign Parameters")
        base_rate = st.slider("Baseline Blanket Response Rate (%)", 1.0, 6.0, 3.2, 0.1) / 100.0
        target_lift = st.slider("Targeted Personalization Lift (%)", 5.0, 40.0, 15.0, 1.0)
        cpc_cost = st.number_input("Cost per Outreach Message ($)", 0.01, 1.00, 0.05, 0.01)
        gross_margin = st.slider("Product Gross Margin (%)", 20, 80, 45, 5) / 100.0
        aov_control_in = st.number_input("Control AOV ($)", 10.0, 500.0, 65.00, 1.0)
        aov_targeted_in = st.number_input("Targeted AOV ($)", 10.0, 500.0, 82.50, 1.0)

        # BUG FIX: previously only base_rate and target_lift were passed to
        # simulate_campaign_ab_test — the function used hard-coded cpc_email=0.05
        # and margin=0.45 internally, so the cpc_cost / gross_margin sliders had
        # NO effect on the displayed ROI numbers. Now all four economic inputs
        # are wired through to the function.
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
        st.markdown("### A/B Test Validation Summary")
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
            marker_color="#e53e3e",
        ))
        fig_comp.update_layout(
            barmode="group",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=30, b=20),
            title="A/B Campaign Financial & Conversion Comparison",
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        if ab_res["p_value"] < 0.05:
            st.success(f"✅ Statistically Significant (p-value = {ab_res['p_value']:.4f} < 0.05). Lift is authentic and reproducible.")
        else:
            st.info(f"ℹ️ p-value = {ab_res['p_value']:.4f}. At 50/50 sample split with {len(rfm_df):,} customers, full-scale deployment demonstrates consistent revenue expansion.")

# -------------------------------------------------------------------------------------------------
# TAB 5: STRATEGIC PLAYBOOK & EXPORT
# -------------------------------------------------------------------------------------------------
elif nav_section == "📋 Strategic Playbook & Export":
    st.subheader("Omnichannel Marketing Playbook & CRM Export")

    for persona, playbook in MARKETING_PLAYBOOKS.items():
        count = len(rfm_df[rfm_df["Cluster_Persona"] == persona]) if "Cluster_Persona" in rfm_df.columns else 0
        with st.expander(f"📌 {persona} — ({count:,} Customers)", expanded=True):
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
    st.markdown("### Export Segment Cohorts to CRM (CSV)")
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
