"""Delegation Patterns Analysis Page

This page provides visualizations and metrics for delegation pattern analysis,
showing how voting power is delegated and flows between addresses.
"""

import json
import os
import sys
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(current_dir)
src_dir = os.path.dirname(dashboard_dir)
sys.path.insert(0, os.path.dirname(src_dir))

from src.analyzer.config import DEFAULT_OUTPUT_DIR

st.set_page_config(
    page_title="Delegation Patterns Analysis", page_icon="🔄", layout="wide"
)

st.title("Delegation Patterns Analysis")
st.sidebar.markdown("# Delegation Patterns")

# Protocol selection
protocol = st.sidebar.selectbox("Select Protocol", ["Compound", "Uniswap", "Aave"])


# Helper function to load analysis data
def load_analysis_data(protocol):
    """Load analysis data for the selected protocol."""
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    file_path = output_dir / f"{protocol.lower()}_analysis.json"

    try:
        with open(file_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading data for {protocol}: {str(e)}")
        return None


# Load data
data = load_analysis_data(protocol)

if data and "delegation_patterns" in data:
    delegation_data = data["delegation_patterns"]

    # Display protocol info
    st.markdown(f"## {data.get('name', protocol)} ({data.get('symbol', '')})")

    # Summary metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delegator_count = delegation_data.get("total_delegators", 0)
        st.metric("Total Delegators", delegator_count)
        st.caption("Addresses delegating voting power")

    with col2:
        delegatee_count = delegation_data.get("total_delegatees", 0)
        st.metric("Total Delegatees", delegatee_count)
        st.caption("Addresses receiving delegations")

    with col3:
        delegated_power = delegation_data.get("total_delegated_power", 0)
        st.metric("Delegated Power", f"{delegated_power:,.2f}")
        st.caption("Total voting power delegated")

    with col4:
        delegation_pct = delegation_data.get("delegation_percentage", 0)
        st.metric("Delegation %", f"{delegation_pct:.2f}%")
        st.caption("% of total voting power delegated")

    # Main content area
    tab1, tab2, tab3 = st.tabs(
        ["Delegation Overview", "Network Visualization", "Delegation Metrics"]
    )

    with tab1:
        st.subheader("Delegation Overview")

        # Top delegatees table
        if "top_delegatees" in delegation_data:
            st.markdown("### Top Delegatees")

            top_delegatees = delegation_data["top_delegatees"]

            delegatees_data = []
            for delegatee in top_delegatees:
                delegatees_data.append(
                    {
                        "Address": delegatee["address"],
                        "Delegated Power": f"{delegatee['delegated_power']:,.2f}",
                        "Delegated Power %": f"{delegatee['delegated_power_percentage']:.2f}%",
                        "Delegator Count": delegatee["delegator_count"],
                    }
                )

            delegatees_df = pd.DataFrame(delegatees_data)
            st.dataframe(delegatees_df, use_container_width=True)

            # Visualize top delegatees
            st.subheader("Top Delegatees by Delegated Power")

            # Convert to numeric for visualization
            viz_data = pd.DataFrame(top_delegatees)

            # Use only top 10 for clearer visualization
            viz_data = viz_data.head(10)

            # Create short address labels
            viz_data["short_address"] = viz_data["address"].apply(
                lambda x: f"{x[:6]}...{x[-4:]}"
            )

            fig = px.bar(
                viz_data,
                x="short_address",
                y="delegated_power_percentage",
                title=f"Top 10 Delegatees in {protocol}",
                labels={
                    "short_address": "Delegatee Address",
                    "delegated_power_percentage": "Delegated Power (%)",
                },
                color="delegator_count",
                color_continuous_scale=px.colors.sequential.Viridis,
                hover_data=["delegated_power", "delegator_count"],
            )

            st.plotly_chart(fig, use_container_width=True)

        # Delegation distribution
        if "delegation_distribution" in delegation_data:
            st.subheader("Delegation Distribution")

            distribution = delegation_data["delegation_distribution"]

            # Create a DataFrame for visualization
            distribution_data = []

            for category, value in distribution.items():
                # Format category name for display
                formatted_category = " ".join(
                    word.capitalize() for word in category.split("_")
                )

                distribution_data.append(
                    {"Category": formatted_category, "Percentage": value}
                )

            distribution_df = pd.DataFrame(distribution_data)

            # Create pie chart
            fig = px.pie(
                distribution_df,
                values="Percentage",
                names="Category",
                title=f"Delegation Distribution in {protocol}",
                color_discrete_sequence=px.colors.qualitative.Plotly,
            )

            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Delegation Network Visualization")

        # Network visualization settings
        st.sidebar.markdown("## Network Settings")
        show_labels = st.sidebar.checkbox("Show Address Labels", value=False)
        min_delegation = st.sidebar.slider(
            "Minimum Delegation Amount (%)", 0.0, 5.0, 0.1
        )

        # Create network visualization using NetworkX and Plotly
        if "delegation_network" in delegation_data:
            network = delegation_data["delegation_network"]

            # Create a graph
            G = nx.DiGraph()  # Directed graph for delegations

            # Add nodes (addresses)
            for node in network["nodes"]:
                G.add_node(
                    node["id"],
                    voting_power=node.get("voting_power", 0),
                    delegated_power=node.get("delegated_power", 0),
                    is_delegatee=node.get("is_delegatee", False),
                )

            # Add edges (delegations)
            for edge in network["edges"]:
                if edge.get("weight", 0) >= min_delegation:
                    G.add_edge(
                        edge["source"],
                        edge["target"],
                        weight=edge["weight"],
                        amount=edge.get("amount", 0),
                    )

            # Calculate layout - use a circular layout for delegations
            if len(G.nodes()) > 0:
                pos = nx.spring_layout(G, k=0.5, iterations=50)

                # Create edge traces
                edge_traces = []
                for edge in G.edges(data=True):
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    weight = edge[2]["weight"]
                    amount = edge[2].get("amount", 0)

                    edge_trace = go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        line=dict(width=weight * 3, color="rgba(150,150,150,0.7)"),
                        hoverinfo="text",
                        text=f"Delegation: {edge[0][:6]}...{edge[0][-4:]} → {edge[1][:6]}...{edge[1][-4:]}<br>Amount: {amount:,.2f}<br>Weight: {weight:.2f}%",
                        mode="lines",
                    )
                    edge_traces.append(edge_trace)

                # Create delegator node trace
                delegator_nodes = [
                    node for node in G.nodes() if not G.nodes[node]["is_delegatee"]
                ]
                delegator_trace = go.Scatter(
                    x=[pos[node][0] for node in delegator_nodes],
                    y=[pos[node][1] for node in delegator_nodes],
                    mode="markers",
                    marker=dict(
                        size=[
                            G.nodes[node].get("voting_power", 1) * 5 + 5
                            for node in delegator_nodes
                        ],
                        color="blue",
                        line=dict(width=1, color="rgb(50,50,50)"),
                    ),
                    text=[
                        f"Delegator: {node[:6]}...{node[-4:]}<br>Voting Power: {G.nodes[node].get('voting_power', 0):,.2f}"
                        for node in delegator_nodes
                    ],
                    hoverinfo="text",
                    name="Delegators",
                )

                # Create delegatee node trace
                delegatee_nodes = [
                    node for node in G.nodes() if G.nodes[node]["is_delegatee"]
                ]
                delegatee_trace = go.Scatter(
                    x=[pos[node][0] for node in delegatee_nodes],
                    y=[pos[node][1] for node in delegatee_nodes],
                    mode="markers",
                    marker=dict(
                        size=[
                            G.nodes[node].get("delegated_power", 1) * 5 + 10
                            for node in delegatee_nodes
                        ],
                        color="red",
                        line=dict(width=1, color="rgb(50,50,50)"),
                    ),
                    text=[
                        f"Delegatee: {node[:6]}...{node[-4:]}<br>Delegated Power: {G.nodes[node].get('delegated_power', 0):,.2f}"
                        for node in delegatee_nodes
                    ],
                    hoverinfo="text",
                    name="Delegatees",
                )

                # Create the figure
                fig = go.Figure(data=edge_traces + [delegator_trace, delegatee_trace])

                # Add node labels if requested
                if show_labels:
                    annotations = []
                    for node in G.nodes():
                        annotations.append(
                            dict(
                                x=pos[node][0],
                                y=pos[node][1],
                                text=f"{node[:6]}...{node[-4:]}",
                                showarrow=False,
                                font=dict(size=8),
                            )
                        )

                    fig.update_layout(annotations=annotations)

                fig.update_layout(
                    title=f"Delegation Network for {protocol}",
                    showlegend=True,
                    hovermode="closest",
                    margin=dict(b=0, l=0, r=0, t=40),
                    height=700,
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No delegation data meeting the minimum threshold.")
        else:
            st.info("Delegation network data not available for this protocol.")

    with tab3:
        st.subheader("Delegation Metrics & Analysis")

        # Delegation classification
        if "delegation_classification" in delegation_data:
            st.markdown("### Delegation Classification")

            classification = delegation_data["delegation_classification"]

            # Create a DataFrame for visualization
            class_data = []

            for category, count in classification.items():
                # Format category name for display
                formatted_category = " ".join(
                    word.capitalize() for word in category.split("_")
                )

                class_data.append({"Category": formatted_category, "Count": count})

            class_df = pd.DataFrame(class_data)

            # Create bar chart
            fig = px.bar(
                class_df,
                x="Category",
                y="Count",
                title=f"Delegation Classification in {protocol}",
                color="Count",
                color_continuous_scale=px.colors.sequential.Viridis,
            )

            st.plotly_chart(fig, use_container_width=True)

        # Delegation concentration metrics
        if "delegation_concentration" in delegation_data:
            st.markdown("### Delegation Concentration Metrics")

            concentration = delegation_data["delegation_concentration"]

            metrics_data = []
            for metric, value in concentration.items():
                # Format metric name for display
                formatted_metric = " ".join(
                    word.capitalize() for word in metric.split("_")
                )

                if "percentage" in metric or "ratio" in metric:
                    formatted_value = f"{value:.2f}%"
                elif "index" in metric or "coefficient" in metric:
                    formatted_value = f"{value:.4f}"
                else:
                    formatted_value = f"{value:,.2f}"

                metrics_data.append(
                    {"Metric": formatted_metric, "Value": formatted_value}
                )

            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True)

        # Historical delegation trends
        if "historical_delegation" in delegation_data:
            st.markdown("### Historical Delegation Trends")

            historical = delegation_data["historical_delegation"]

            # Convert to DataFrame
            hist_df = pd.DataFrame(historical)

            # Ensure timestamp is datetime
            if "timestamp" in hist_df.columns:
                hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"])

            # Create line chart
            fig = px.line(
                hist_df,
                x="timestamp",
                y="delegation_percentage",
                title=f"Delegation Percentage Over Time in {protocol}",
                labels={
                    "timestamp": "Date",
                    "delegation_percentage": "Delegation Percentage (%)",
                },
                markers=True,
            )

            # Add trend line if enough data points
            if len(hist_df) > 1:
                fig.add_traces(
                    px.scatter(
                        hist_df,
                        x="timestamp",
                        y="delegation_percentage",
                        trendline="ols",
                    ).data[1]
                )

            st.plotly_chart(fig, use_container_width=True)
else:
    st.error(f"Unable to load delegation data for {protocol}")
    st.info(
        "Please make sure you've run the delegation pattern analysis for this protocol first. Note that not all protocols support delegation."
    )
