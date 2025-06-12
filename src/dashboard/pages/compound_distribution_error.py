"""Compound Token Distribution Page

This page shows detailed analysis of the Compound governance token (COMP) distribution.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analyzer.config import DEFAULT_OUTPUT_DIR
from src.analyzer.token_analysis import ConcentrationAnalyzer


# Load analysis data
def load_compound_data():
    """Load Compound analysis data."""
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    file_path = output_dir / "compound_analysis.json"

    try:
        with open(file_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading Compound data: {str(e)}")
        return None


# Page title
st.title("Compound Token Distribution Analysis")

# Load data
data = load_compound_data()

# Display data or error message
if data:
    # Top Holders Section
    st.header("Top Token Holders")

    if "top_holders" in data:
        top_holders_df = pd.DataFrame(data["top_holders"])
        st.dataframe(top_holders_df)
    else:
        st.info("Top holders data not available")

    # Concentration Metrics
    st.header("Concentration Metrics")

    col1, col2 = st.columns(2)

    with col1:
        if "concentration_metrics" in data:
            metrics = data["concentration_metrics"]
            st.metric(
                "Gini Coefficient", f"{metrics.get('gini_coefficient', 'N/A'):.4f}"
            )
            st.metric(
                "Herfindahl Index", f"{metrics.get('herfindahl_index', 'N/A'):.4f}"
            )

            # Show CR metrics in expandable section
            with st.expander("Concentration Ratios"):
                if "top_holders_percentage" in metrics:
                    for k, v in metrics["top_holders_percentage"].items():
                        st.metric(f"CR{k}", f"{v:.2f}%")
        else:
            st.info("Concentration metrics not available")

    with col2:
        if (
            "concentration_metrics" in data
            and "lorenz_curve" in data["concentration_metrics"]
        ):
            lorenz_data = data["concentration_metrics"]["lorenz_curve"]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[0] + lorenz_data["x"],
                    y=[0] + lorenz_data["y"],
                    mode="lines",
                    name="Lorenz Curve",
                    line=dict(color="blue"),
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

            fig.update_layout(
                title="Lorenz Curve - Token Distribution Inequality",
                xaxis_title="Cumulative % of Holders",
                yaxis_title="Cumulative % of Tokens",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Lorenz curve data not available")

    # Distribution Visualization
    st.header("Distribution Visualization")

    if "top_holders" in data:
        top_n = st.slider("Number of top holders to display", 5, 20, 10)

        holders = data["top_holders"][:top_n]
        others_pct = 100 - sum(h["percentage"] for h in holders)

        labels = [
            f"#{h['rank']}: {h['address'][:6]}...{h['address'][-4:]}" for h in holders
        ]
        values = [h["percentage"] for h in holders]

        if others_pct > 0:
            labels.append("Others")
            values.append(others_pct)

        fig = px.pie(
            values=values,
            names=labels,
            title="Compound Token Distribution",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Holder distribution data not available")

    # Advanced Metrics
    st.header("Advanced Concentration Metrics")

    if "concentration_metrics" in data:
        metrics = data["concentration_metrics"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Nakamoto Coefficient", metrics.get("nakamoto_coefficient", "N/A")
            )

        with col2:
            st.metric("Palma Ratio", f"{metrics.get('palma_ratio', 'N/A'):.2f}")

        with col3:
            st.metric("Theil Index", f"{metrics.get('theil_index', 'N/A'):.4f}")

        # Show additional metrics in expandable section
        with st.expander("Additional Metrics"):
            st.metric("Hoover Index", f"{metrics.get('hoover_index', 'N/A'):.4f}")

            if "top_percentile_concentration" in metrics:
                st.subheader("Top Percentile Concentration")

                percentiles = metrics["top_percentile_concentration"]
                fig = px.bar(
                    x=list(percentiles.keys()),
                    y=list(percentiles.values()),
                    labels={
                        "x": "Top N% of Holders",
                        "y": "Percentage of Total Tokens",
                    },
                    title="Token Concentration by Top Percentiles",
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Advanced concentration metrics not available")
else:
    st.error("Failed to load Compound token distribution data")

    # Display fallback options
    st.info("You can try the following:")
    st.markdown("""
    1. Run the data collection script to gather Compound token data
    2. Check that the API keys are correctly configured
    3. Verify that the output directory exists and is writable
    """)

    # Option to run analysis directly
    if st.button("Run Compound Analysis"):
        with st.spinner("Analyzing Compound token distribution..."):
            try:
                analyzer = ConcentrationAnalyzer()
                results = analyzer.analyze_protocol_concentration("compound")

                if results:
                    st.success("Analysis completed successfully!")
                    st.json(results)
                else:
                    st.error("Analysis returned no results")
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
