"""Token Distribution Analysis Page

This page provides visualizations and metrics for token distribution analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(current_dir)
src_dir = os.path.dirname(dashboard_dir)
sys.path.insert(0, os.path.dirname(src_dir))

from src.analyzer.config import DEFAULT_OUTPUT_DIR

st.set_page_config(page_title="Token Distribution Analysis", page_icon="📊", layout="wide")

st.title("Token Distribution Analysis")
st.sidebar.markdown("# Token Distribution")

# Protocol selection
protocol = st.sidebar.selectbox("Select Protocol", ["Compound", "Uniswap", "Aave"])


# Helper function to load analysis data
def load_analysis_data(protocol):
    """Load analysis data for the selected protocol."""
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    file_path = output_dir / f"{protocol.lower()}_analysis.json"

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading data for {protocol}: {str(e)}")
        return None


# Load data
data = load_analysis_data(protocol)

if data:
    # Display token info
    st.markdown(f"## {data.get('name', protocol)} ({data.get('symbol', '')})")

    # Summary metrics in columns
    if "concentration_metrics" in data:
        metrics = data["concentration_metrics"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Gini Coefficient", f"{metrics.get('gini_coefficient', 'N/A'):.4f}")
            st.caption("0 = perfect equality, 1 = perfect inequality")

        with col2:
            st.metric("Herfindahl Index", f"{metrics.get('herfindahl_index', 'N/A'):.4f}")
            st.caption("Measures market concentration")

        with col3:
            nakamoto = metrics.get("nakamoto_coefficient", "N/A")
            st.metric("Nakamoto Coefficient", nakamoto)
            st.caption("Entities needed for 51% control")

        with col4:
            if "top_holders_percentage" in metrics and 10 in metrics["top_holders_percentage"]:
                cr10 = metrics["top_holders_percentage"][10]
                st.metric("Top 10 Concentration", f"{cr10:.2f}%")
                st.caption("% held by top 10 addresses")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["Holder Analysis", "Concentration Metrics", "Visualization"])

    with tab1:
        st.subheader("Top Token Holders")

        # Display top holders table
        if "top_holders" in data:
            top_n = st.slider("Number of top holders to display", 5, 50, 20, key="top_holders_slider")

            # Create DataFrame from top holders
            holders_df = pd.DataFrame(data["top_holders"][:top_n])

            # Format the data
            if "percentage" in holders_df.columns:
                holders_df["percentage"] = holders_df["percentage"].apply(lambda x: f"{x:.2f}%")

            if "balance" in holders_df.columns:
                holders_df["balance"] = holders_df["balance"].apply(lambda x: f"{x:,.2f}")

            st.dataframe(holders_df, use_container_width=True)

        # Whale Addresses
        if "whale_addresses" in data:
            with st.expander("Whale Addresses (>1% of supply)"):
                whales_df = pd.DataFrame(data["whale_addresses"])
                st.dataframe(whales_df, use_container_width=True)

    with tab2:
        st.subheader("Detailed Concentration Metrics")

        if "concentration_metrics" in data:
            metrics = data["concentration_metrics"]

            # Create two columns for metrics
            col1, col2 = st.columns(2)

            with col1:
                # Basic metrics
                st.markdown("### Basic Metrics")
                metrics_df = pd.DataFrame(
                    {
                        "Metric": [
                            "Gini Coefficient",
                            "Herfindahl Index",
                            "Nakamoto Coefficient",
                            "Hoover Index",
                            "Theil Index",
                        ],
                        "Value": [
                            f"{metrics.get('gini_coefficient', 'N/A'):.4f}",
                            f"{metrics.get('herfindahl_index', 'N/A'):.4f}",
                            metrics.get("nakamoto_coefficient", "N/A"),
                            f"{metrics.get('hoover_index', 'N/A'):.4f}",
                            f"{metrics.get('theil_index', 'N/A'):.4f}",
                        ],
                        "Interpretation": [
                            "0 = perfect equality, 1 = perfect inequality",
                            "Market concentration (>0.25 is concentrated)",
                            "Entities needed for 51% control",
                            "Proportion needed for redistribution to equality",
                            "Information-theoretic measure of inequality",
                        ],
                    }
                )

                st.dataframe(metrics_df, hide_index=True, use_container_width=True)

            with col2:
                # Concentration ratios
                st.markdown("### Concentration Ratios")
                if "top_holders_percentage" in metrics:
                    cr_data = []

                    for k, v in sorted(
                        metrics["top_holders_percentage"].items(),
                        key=lambda x: int(x[0]),
                    ):
                        cr_data.append(
                            {
                                "Top N Holders": f"Top {k} Holders",
                                "Percentage": f"{v:.2f}%",
                            }
                        )

                    cr_df = pd.DataFrame(cr_data)
                    st.dataframe(cr_df, hide_index=True, use_container_width=True)

        # If there are palma ratio or other advanced metrics
        if "concentration_metrics" in data and "palma_ratio" in data["concentration_metrics"]:
            st.markdown("### Advanced Inequality Metrics")
            advanced_df = pd.DataFrame(
                {
                    "Metric": ["Palma Ratio", "20:20 Ratio", "Share of Top 1%"],
                    "Value": [
                        f"{metrics.get('palma_ratio', 'N/A'):.2f}",
                        f"{metrics.get('ratio_20_20', 'N/A'):.2f}",
                        f"{metrics.get('top_percentiles', {}).get('1', 'N/A'):.2f}%",
                    ],
                    "Interpretation": [
                        "Ratio of top 10% to bottom 40% holdings",
                        "Ratio of top 20% to bottom 20% holdings",
                        "Percentage of tokens held by top 1% of addresses",
                    ],
                }
            )

            st.dataframe(advanced_df, hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("Distribution Visualizations")

        viz_type = st.radio(
            "Select Visualization Type",
            ["Pie Chart", "Lorenz Curve", "Concentration Bars"],
            horizontal=True,
        )

        if viz_type == "Pie Chart":
            # Pie chart for token distribution
            if "top_holders" in data:
                top_n = st.slider("Number of top holders in chart", 5, 20, 10, key="pie_chart_slider")

                holders = data["top_holders"][:top_n]
                others_pct = 100 - sum(h["percentage"] for h in holders)

                labels = [f"#{h['rank']}: {h['address'][:6]}...{h['address'][-4:]}" for h in holders]
                values = [h["percentage"] for h in holders]

                if others_pct > 0:
                    labels.append("Others")
                    values.append(others_pct)

                fig = px.pie(
                    values=values,
                    names=labels,
                    title=f"{protocol} Token Distribution",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Prism,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "Lorenz Curve":
            # Lorenz curve visualization
            if "lorenz_curve" in data:
                lorenz_data = data["lorenz_curve"]

                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=[0] + lorenz_data["x"],
                        y=[0] + lorenz_data["y"],
                        mode="lines",
                        name="Lorenz Curve",
                        line=dict(color="blue", width=2),
                    )
                )

                # Add perfect equality line
                fig.add_trace(
                    go.Scatter(
                        x=[0, 1],
                        y=[0, 1],
                        mode="lines",
                        name="Perfect Equality",
                        line=dict(color="red", dash="dash"),
                    )
                )

                # Calculate and highlight the Gini coefficient area
                if "concentration_metrics" in data and "gini_coefficient" in data["concentration_metrics"]:
                    gini = data["concentration_metrics"]["gini_coefficient"]

                    # Add shading for Gini coefficient
                    x_values = [0] + lorenz_data["x"]
                    y_values = [0] + lorenz_data["y"]
                    line_x = list(np.linspace(0, 1, 100))
                    line_y = line_x

                    # Annotation for Gini coefficient
                    fig.add_annotation(
                        x=0.5,
                        y=0.2,
                        text=f"Gini Coefficient: {gini:.4f}",
                        showarrow=False,
                        font=dict(size=14),
                    )

                fig.update_layout(
                    title="Lorenz Curve - Token Distribution Inequality",
                    xaxis_title="Cumulative % of Holders",
                    yaxis_title="Cumulative % of Tokens",
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                )
                st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "Concentration Bars":
            # Bar chart for concentration ratios
            if "concentration_metrics" in data and "top_holders_percentage" in data["concentration_metrics"]:
                cr_data = data["concentration_metrics"]["top_holders_percentage"]

                # Sort by holder count
                sorted_keys = sorted(cr_data.keys(), key=lambda x: int(x))

                fig = px.bar(
                    x=[f"Top {k}" for k in sorted_keys],
                    y=[cr_data[k] for k in sorted_keys],
                    title="Token Concentration by Holder Group",
                    labels={"x": "Holder Group", "y": "% of Total Supply"},
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )

                # Add a horizontal line at 50% for reference
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=50,
                    x1=len(sorted_keys) - 0.5,
                    y1=50,
                    line=dict(color="red", width=2, dash="dash"),
                )

                # Add annotation for the 50% line
                fig.add_annotation(
                    x=len(sorted_keys) / 2,
                    y=52,
                    text="50% Control Threshold",
                    showarrow=False,
                    font=dict(color="red"),
                )

                st.plotly_chart(fig, use_container_width=True)
else:
    st.error(f"Unable to load analysis data for {protocol}")
    st.info("Please make sure you've run the token analysis for this protocol first.")
