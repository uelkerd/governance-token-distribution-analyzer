"""
Governance Token Distribution Analyzer - Dashboard

This Streamlit application provides interactive visualizations of governance token 
distribution data, participation metrics, voting patterns, and cross-protocol comparisons.
"""

import os
import sys
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, os.path.dirname(src_dir))

from src.analyzer.config import DEFAULT_OUTPUT_DIR
from src.analyzer.token_analysis import ConcentrationAnalyzer
from src.analyzer.governance_metrics import ParticipationAnalyzer
from src.analyzer.advanced_metrics import VotingBlockAnalyzer, DelegationAnalyzer

# Set page configuration
st.set_page_config(
    page_title="Governance Token Distribution Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard title and description
st.title("Governance Token Distribution Analyzer")
st.markdown("""
This dashboard provides interactive visualizations and insights for analyzing governance token 
distribution, participation metrics, voting patterns, and cross-protocol comparisons.
""")

# Sidebar for navigation and controls
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Token Distribution", "Governance Participation", "Voting Blocks", 
     "Delegation Patterns", "Historical Analysis", "Cross-Protocol Comparison"]
)

# Protocol selection
st.sidebar.title("Settings")
protocol = st.sidebar.selectbox(
    "Select Protocol",
    ["Compound", "Uniswap", "Aave"]
)

# Helper function to load analysis data
def load_analysis_data(protocol):
    """Load analysis data for the selected protocol."""
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    file_path = output_dir / f"{protocol.lower()}_analysis.json"
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading data for {protocol}: {str(e)}")
        return None

# Token Distribution Page
if page == "Token Distribution":
    st.header("Token Distribution Analysis")
    
    data = load_analysis_data(protocol)
    if data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Token Holders")
            
            # Create a DataFrame for the top holders
            if 'top_holders' in data:
                top_holders_df = pd.DataFrame(data['top_holders'])
                st.dataframe(top_holders_df)
            else:
                st.info("Top holders data not available")
            
            # Display concentration metrics
            st.subheader("Concentration Metrics")
            if 'concentration_metrics' in data:
                metrics = data['concentration_metrics']
                st.metric("Gini Coefficient", f"{metrics.get('gini_coefficient', 'N/A'):.4f}")
                st.metric("Herfindahl Index", f"{metrics.get('herfindahl_index', 'N/A'):.4f}")
                
                # Show CR metrics in expandable section
                with st.expander("Concentration Ratios"):
                    if 'top_holders_percentage' in metrics:
                        for k, v in metrics['top_holders_percentage'].items():
                            st.metric(f"CR{k}", f"{v:.2f}%")
            else:
                st.info("Concentration metrics not available")
        
        with col2:
            st.subheader("Distribution Visualization")
            
            # Create pie chart for top holders
            if 'top_holders' in data:
                top_n = st.slider("Number of top holders to display", 5, 20, 10)
                
                holders = data['top_holders'][:top_n]
                others_pct = 100 - sum(h['percentage'] for h in holders)
                
                labels = [f"#{h['rank']}: {h['address'][:6]}...{h['address'][-4:]}" for h in holders]
                values = [h['percentage'] for h in holders]
                
                if others_pct > 0:
                    labels.append("Others")
                    values.append(others_pct)
                
                fig = px.pie(
                    values=values,
                    names=labels,
                    title=f"{protocol} Token Distribution",
                    hole=0.4,
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            # Create Lorenz curve if data available
            if 'lorenz_curve' in data:
                st.subheader("Lorenz Curve")
                lorenz_data = data['lorenz_curve']
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[0] + lorenz_data['x'],
                    y=[0] + lorenz_data['y'],
                    mode='lines',
                    name='Lorenz Curve',
                    line=dict(color='blue')
                ))
                
                # Add perfect equality line
                fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode='lines',
                    name='Perfect Equality',
                    line=dict(color='red', dash='dash')
                ))
                
                fig.update_layout(
                    title='Lorenz Curve - Token Distribution Inequality',
                    xaxis_title='Cumulative % of Holders',
                    yaxis_title='Cumulative % of Tokens',
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                )
                st.plotly_chart(fig, use_container_width=True)

# Governance Participation Page
elif page == "Governance Participation":
    st.header("Governance Participation Analysis")
    
    data = load_analysis_data(protocol)
    if data and 'governance_metrics' in data:
        gov_metrics = data['governance_metrics']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Participation Rate", f"{gov_metrics.get('participation_rate', 'N/A'):.2f}%")
        with col2:
            st.metric("Total Proposals", gov_metrics.get('total_proposals', 'N/A'))
        with col3:
            st.metric("Active Voters", gov_metrics.get('active_voters', 'N/A'))
        
        # Proposal Participation Chart
        if 'proposal_participation' in gov_metrics:
            st.subheader("Proposal Participation")
            prop_data = pd.DataFrame(gov_metrics['proposal_participation'])
            
            fig = px.bar(
                prop_data,
                x='proposal_id',
                y='participation_rate',
                title=f"Participation Rate by Proposal in {protocol}",
                labels={'proposal_id': 'Proposal ID', 'participation_rate': 'Participation Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Voter Segments
        if 'voter_segments' in gov_metrics:
            st.subheader("Voter Segmentation")
            segments = gov_metrics['voter_segments']
            
            fig = px.pie(
                values=[segments.get(k, 0) for k in ['highly_active', 'active', 'occasional', 'inactive']],
                names=['Highly Active', 'Active', 'Occasional', 'Inactive'],
                title="Voter Activity Segmentation",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Governance participation data not available for {protocol}")

# Placeholder for other pages
elif page == "Voting Blocks":
    st.header("Voting Block Analysis")
    st.info("Detailed voting block visualization will be implemented here.")
    
elif page == "Delegation Patterns":
    st.header("Delegation Pattern Analysis") 
    st.info("Delegation network visualization will be implemented here.")
    
elif page == "Historical Analysis":
    st.header("Historical Data Analysis")
    st.info("Time series analysis of token distribution and governance metrics will be implemented here.")
    
elif page == "Cross-Protocol Comparison":
    st.header("Cross-Protocol Comparison")
    st.info("Comparative analysis across protocols will be implemented here.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "Governance Token Distribution Analyzer Dashboard - v1.0.0"
)

# Run the app with: streamlit run src/dashboard/app.py 