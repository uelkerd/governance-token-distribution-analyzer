"""Governance Participation Analysis Page

This page provides visualizations and metrics for governance participation analysis.
"""

import streamlit as st
import pandas as pd
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

st.set_page_config(page_title="Governance Participation Analysis", page_icon="🗳️", layout="wide")

st.title("Governance Participation Analysis")
st.sidebar.markdown("# Governance Participation")

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

if data and "governance_metrics" in data:
    gov_metrics = data["governance_metrics"]

    # Display protocol info
    st.markdown(f"## {data.get('name', protocol)} ({data.get('symbol', '')})")

    # Summary metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        participation_rate = gov_metrics.get("participation_rate", 0)
        st.metric("Participation Rate", f"{participation_rate:.2f}%")
        st.caption("Average % of total voting power used")

    with col2:
        total_proposals = gov_metrics.get("total_proposals", 0)
        st.metric("Total Proposals", total_proposals)
        st.caption("Number of governance proposals")

    with col3:
        active_voters = gov_metrics.get("active_voters", 0)
        st.metric("Active Voters", active_voters)
        st.caption("Number of addresses that voted")

    with col4:
        avg_proposal_turnout = gov_metrics.get("avg_proposal_turnout", 0)
        st.metric("Avg. Proposal Turnout", f"{avg_proposal_turnout:.2f}%")
        st.caption("Average turnout per proposal")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["Proposal Analysis", "Voter Analysis", "Participation Trends"])

    with tab1:
        st.subheader("Governance Proposal Analysis")

        # Display proposal participation data
        if "proposal_participation" in gov_metrics:
            proposal_data = pd.DataFrame(gov_metrics["proposal_participation"])

            # Format the columns
            if "participation_rate" in proposal_data.columns:
                proposal_data["participation_rate"] = proposal_data["participation_rate"].apply(lambda x: f"{x:.2f}%")

            if "votes_for" in proposal_data.columns and "votes_against" in proposal_data.columns:
                proposal_data["support_rate"] = proposal_data.apply(
                    lambda row: f"{float(row['votes_for']) / (float(row['votes_for']) + float(row['votes_against'])) * 100:.2f}%"
                    if float(row["votes_for"]) + float(row["votes_against"]) > 0
                    else "N/A",
                    axis=1,
                )

            # Display the proposal data table
            st.dataframe(proposal_data, use_container_width=True)

            # Visualize proposal participation
            st.subheader("Proposal Participation Rates")

            # Convert string percentages back to floats for visualization
            viz_data = pd.DataFrame(gov_metrics["proposal_participation"])

            fig = px.bar(
                viz_data,
                x="proposal_id",
                y="participation_rate",
                title=f"Participation Rate by Proposal in {protocol}",
                labels={
                    "proposal_id": "Proposal ID",
                    "participation_rate": "Participation Rate (%)",
                },
                color="participation_rate",
                color_continuous_scale=px.colors.sequential.Viridis,
            )

            # Add a horizontal line for average participation
            fig.add_shape(
                type="line",
                x0=-0.5,
                y0=participation_rate,
                x1=len(viz_data) - 0.5,
                y1=participation_rate,
                line=dict(color="red", width=2, dash="dash"),
            )

            # Add annotation for the average line
            fig.add_annotation(
                x=len(viz_data) / 2,
                y=participation_rate + 2,
                text=f"Average: {participation_rate:.2f}%",
                showarrow=False,
                font=dict(color="red"),
            )

            st.plotly_chart(fig, use_container_width=True)

            # If we have votes for/against data, visualize proposal outcomes
            if "votes_for" in viz_data.columns and "votes_against" in viz_data.columns:
                st.subheader("Proposal Voting Outcomes")

                # Convert votes to numeric
                viz_data["votes_for"] = pd.to_numeric(viz_data["votes_for"])
                viz_data["votes_against"] = pd.to_numeric(viz_data["votes_against"])

                # Calculate total votes and support rate
                viz_data["total_votes"] = viz_data["votes_for"] + viz_data["votes_against"]
                viz_data["support_rate"] = viz_data["votes_for"] / viz_data["total_votes"] * 100

                # Create stacked bar chart
                fig = go.Figure()

                fig.add_trace(
                    go.Bar(
                        x=viz_data["proposal_id"],
                        y=viz_data["votes_for"],
                        name="Votes For",
                        marker_color="rgb(55, 83, 109)",
                    )
                )

                fig.add_trace(
                    go.Bar(
                        x=viz_data["proposal_id"],
                        y=viz_data["votes_against"],
                        name="Votes Against",
                        marker_color="rgb(219, 64, 82)",
                    )
                )

                fig.update_layout(
                    title=f"{protocol} Proposal Voting Results",
                    xaxis_title="Proposal ID",
                    yaxis_title="Votes",
                    barmode="stack",
                )

                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Voter Analysis")

        # Voter segments visualization
        if "voter_segments" in gov_metrics:
            segments = gov_metrics["voter_segments"]

            # Create a DataFrame for the segments
            segment_labels = {
                "highly_active": "Highly Active (>75% proposals)",
                "active": "Active (25-75% proposals)",
                "occasional": "Occasional (<25% proposals)",
                "inactive": "Inactive (0 proposals)",
            }

            segment_data = []
            for k, label in segment_labels.items():
                segment_data.append(
                    {
                        "Segment": label,
                        "Count": segments.get(k, 0),
                        "Order": list(segment_labels.keys()).index(k),
                    }
                )

            # Sort by the defined order
            segment_df = pd.DataFrame(segment_data).sort_values("Order")

            # Create pie chart
            fig = px.pie(
                segment_df,
                values="Count",
                names="Segment",
                title="Voter Activity Segmentation",
                color_discrete_sequence=px.colors.sequential.Plasma_r,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")

            st.plotly_chart(fig, use_container_width=True)

        # Top voters by voting power
        if "top_voters" in gov_metrics:
            st.subheader("Top Voters by Voting Power")

            top_voters_df = pd.DataFrame(gov_metrics["top_voters"])

            # Format the columns
            if "voting_power" in top_voters_df.columns:
                top_voters_df["voting_power"] = top_voters_df["voting_power"].apply(lambda x: f"{x:,.2f}")

            if "voting_power_percentage" in top_voters_df.columns:
                top_voters_df["voting_power_percentage"] = top_voters_df["voting_power_percentage"].apply(
                    lambda x: f"{x:.2f}%"
                )

            # Display the top voters table
            st.dataframe(top_voters_df, use_container_width=True)

            # Create bar chart of top voters
            if "address" in top_voters_df.columns and "voting_power_percentage" in top_voters_df.columns:
                # Convert percentage strings back to numbers for visualization
                viz_data = pd.DataFrame(gov_metrics["top_voters"])

                # Limit to top 10 for better visualization
                viz_data = viz_data.head(10)

                # Create short address labels
                viz_data["short_address"] = viz_data["address"].apply(lambda x: f"{x[:6]}...{x[-4:]}")

                fig = px.bar(
                    viz_data,
                    x="short_address",
                    y="voting_power_percentage",
                    title="Top 10 Voters by Voting Power",
                    labels={
                        "short_address": "Voter Address",
                        "voting_power_percentage": "% of Total Voting Power",
                    },
                    color="voting_power_percentage",
                    color_continuous_scale=px.colors.sequential.Viridis,
                )

                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Participation Trends")

        # Historical participation visualization
        if "historical_participation" in gov_metrics:
            historical_data = pd.DataFrame(gov_metrics["historical_participation"])

            # Ensure timestamp is in datetime format
            if "timestamp" in historical_data.columns:
                historical_data["timestamp"] = pd.to_datetime(historical_data["timestamp"])

            # Create line chart of participation over time
            fig = px.line(
                historical_data,
                x="timestamp",
                y="participation_rate",
                title=f"{protocol} Governance Participation Over Time",
                labels={
                    "timestamp": "Date",
                    "participation_rate": "Participation Rate (%)",
                },
                markers=True,
            )

            # Add a trend line
            if len(historical_data) > 1:
                fig.add_traces(
                    px.scatter(
                        historical_data,
                        x="timestamp",
                        y="participation_rate",
                        trendline="ols",
                    ).data[1]
                )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Historical participation data not available for this protocol.")
else:
    st.error(f"Unable to load governance metrics for {protocol}")
    st.info("Please make sure you've run the governance participation analysis for this protocol first.")
