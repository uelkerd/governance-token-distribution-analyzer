"""Voting Blocks Analysis Page

This page provides visualizations and metrics for voting block analysis,
showing coordinated voting behavior and influential voter groups.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
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

st.set_page_config(page_title="Voting Blocks Analysis", page_icon="🔗", layout="wide")

st.title("Voting Blocks Analysis")
st.sidebar.markdown("# Voting Blocks")

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

if data and "voting_blocks" in data:
    voting_blocks = data["voting_blocks"]

    # Display protocol info
    st.markdown(f"## {data.get('name', protocol)} ({data.get('symbol', '')})")

    # Summary metrics in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        block_count = len(voting_blocks.get("blocks", []))
        st.metric("Voting Blocks", block_count)
        st.caption("Number of identified voting blocks")

    with col2:
        total_block_members = sum(len(block["members"]) for block in voting_blocks.get("blocks", []))
        st.metric("Total Block Members", total_block_members)
        st.caption("Total addresses in voting blocks")

    with col3:
        avg_block_cohesion = voting_blocks.get("avg_block_cohesion", 0)
        st.metric("Avg. Block Cohesion", f"{avg_block_cohesion:.2f}%")
        st.caption("Average voting agreement within blocks")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["Block Overview", "Network Visualization", "Block Influence"])

    with tab1:
        st.subheader("Voting Blocks Overview")

        # Create a table of voting blocks
        if "blocks" in voting_blocks:
            blocks_data = []

            for i, block in enumerate(voting_blocks["blocks"]):
                blocks_data.append(
                    {
                        "Block ID": f"Block {i + 1}",
                        "Members": len(block["members"]),
                        "Total Voting Power": f"{block['total_voting_power']:.2f}",
                        "Voting Power %": f"{block['voting_power_percentage']:.2f}%",
                        "Cohesion": f"{block['cohesion']:.2f}%",
                        "Influence Score": f"{block['influence_score']:.2f}",
                    }
                )

            blocks_df = pd.DataFrame(blocks_data)
            st.dataframe(blocks_df, use_container_width=True)

            # Visualize block sizes and voting power
            st.subheader("Voting Block Size vs. Voting Power")

            # Create bubble chart
            fig = px.scatter(
                blocks_data,
                x="Members",
                y="Voting Power %",
                size="Influence Score",
                color="Cohesion",
                hover_name="Block ID",
                title="Voting Block Comparison",
                labels={
                    "Members": "Number of Members",
                    "Voting Power %": "% of Total Voting Power",
                    "Influence Score": "Influence Score",
                    "Cohesion": "Cohesion %",
                },
            )

            st.plotly_chart(fig, use_container_width=True)

            # Block member details
            st.subheader("Voting Block Details")

            selected_block = st.selectbox(
                "Select a voting block to view details",
                [f"Block {i + 1}" for i in range(len(voting_blocks["blocks"]))],
            )

            block_index = int(selected_block.split(" ")[1]) - 1
            block = voting_blocks["blocks"][block_index]

            # Show block members
            members_data = []
            for member in block["members"]:
                members_data.append(
                    {
                        "Address": member["address"],
                        "Voting Power": f"{member['voting_power']:.2f}",
                        "Voting Power %": f"{member['voting_power_percentage']:.2f}%",
                    }
                )

            members_df = pd.DataFrame(members_data)
            st.dataframe(members_df, use_container_width=True)

            # Show voting patterns
            if "voting_patterns" in block:
                st.subheader(f"Voting Patterns for {selected_block}")

                patterns_data = []
                for proposal_id, vote in block["voting_patterns"].items():
                    patterns_data.append(
                        {
                            "Proposal ID": proposal_id,
                            "Vote": "For" if vote == 1 else "Against" if vote == 0 else "Abstain",
                            "Agreement %": f"{block['proposal_agreement'].get(proposal_id, 0):.2f}%",
                        }
                    )

                patterns_df = pd.DataFrame(patterns_data)
                st.dataframe(patterns_df, use_container_width=True)

    with tab2:
        st.subheader("Voting Block Network Visualization")

        # Network visualization settings
        st.sidebar.markdown("## Network Visualization")
        show_labels = st.sidebar.checkbox("Show Address Labels", value=False)
        min_edge_weight = st.sidebar.slider("Minimum Connection Strength", 0.0, 1.0, 0.5)

        # Create network visualization using NetworkX and Plotly
        if "network_data" in voting_blocks:
            network = voting_blocks["network_data"]

            # Create a graph
            G = nx.Graph()

            # Add nodes (voters)
            for node in network["nodes"]:
                G.add_node(
                    node["id"],
                    voting_power=node.get("voting_power", 0),
                    block=node.get("block", -1),
                )

            # Add edges (voting similarities)
            for edge in network["edges"]:
                if edge["weight"] >= min_edge_weight:
                    G.add_edge(edge["source"], edge["target"], weight=edge["weight"])

            # Calculate layout
            pos = nx.spring_layout(G, k=0.5, iterations=50)

            # Create edge traces
            edge_traces = []
            for edge in G.edges(data=True):
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                weight = edge[2]["weight"]

                edge_trace = go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    line=dict(width=weight * 5, color="rgba(150,150,150,0.3)"),
                    hoverinfo="none",
                    mode="lines",
                )
                edge_traces.append(edge_trace)

            # Create node trace
            node_trace = go.Scatter(
                x=[pos[node][0] for node in G.nodes()],
                y=[pos[node][1] for node in G.nodes()],
                mode="markers",
                marker=dict(
                    size=[G.nodes[node].get("voting_power", 1) * 10 + 5 for node in G.nodes()],
                    color=[G.nodes[node].get("block", 0) for node in G.nodes()],
                    colorscale="Viridis",
                    line=dict(width=1, color="rgb(50,50,50)"),
                ),
                text=[
                    f"Address: {node}<br>Voting Power: {G.nodes[node].get('voting_power', 0):.2f}<br>Block: {G.nodes[node].get('block', 'None')}"
                    for node in G.nodes()
                ],
                hoverinfo="text",
            )

            # Create the figure
            fig = go.Figure(data=edge_traces + [node_trace])

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
                title=f"Voting Block Network for {protocol}",
                showlegend=False,
                hovermode="closest",
                margin=dict(b=0, l=0, r=0, t=40),
                height=700,
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Network visualization data not available for this protocol.")

    with tab3:
        st.subheader("Voting Block Influence Analysis")

        # Create influence visualization
        if "blocks" in voting_blocks and "proposal_influence" in voting_blocks:
            # Block influence by proposal
            proposal_influence = voting_blocks["proposal_influence"]

            # Create a DataFrame for visualization
            influence_data = []

            for proposal_id, blocks in proposal_influence.items():
                for block_id, influence in blocks.items():
                    influence_data.append(
                        {
                            "Proposal ID": proposal_id,
                            "Block": f"Block {block_id}",
                            "Influence Score": influence,
                        }
                    )

            if influence_data:
                influence_df = pd.DataFrame(influence_data)

                # Create heatmap
                fig = px.density_heatmap(
                    influence_df,
                    x="Proposal ID",
                    y="Block",
                    z="Influence Score",
                    title=f"Voting Block Influence by Proposal in {protocol}",
                    labels={
                        "Proposal ID": "Proposal ID",
                        "Block": "Voting Block",
                        "Influence Score": "Influence Score",
                    },
                    color_continuous_scale=px.colors.sequential.Viridis,
                )

                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)

            # Overall block influence
            st.subheader("Overall Block Influence")

            blocks_influence = []
            for i, block in enumerate(voting_blocks["blocks"]):
                blocks_influence.append(
                    {
                        "Block": f"Block {i + 1}",
                        "Influence Score": block["influence_score"],
                        "Voting Power": block["voting_power_percentage"],
                        "Members": len(block["members"]),
                    }
                )

            influence_df = pd.DataFrame(blocks_influence)

            fig = px.bar(
                influence_df,
                x="Block",
                y="Influence Score",
                color="Voting Power",
                size="Members",
                title=f"Overall Voting Block Influence in {protocol}",
                labels={
                    "Block": "Voting Block",
                    "Influence Score": "Influence Score",
                    "Voting Power": "Voting Power %",
                    "Members": "Number of Members",
                },
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Block influence data not available for this protocol.")
else:
    st.error(f"Unable to load voting block data for {protocol}")
    st.info("Please make sure you've run the voting block analysis for this protocol first.")
