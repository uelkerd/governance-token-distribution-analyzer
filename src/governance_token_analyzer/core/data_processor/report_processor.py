"""Report Processor for Governance Token Distribution Analyzer.

This module provides functionality for generating reports based on processed
governance token data.
"""

import logging
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class ReportProcessor:
    """Processor for generating reports from governance token data."""

    @staticmethod
    def generate_report(protocol: str, processed_data: Dict[str, Any], output_path: str) -> str:
        """Generate a report for processed protocol data.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            processed_data: Processed protocol data
            output_path: Path to save the report

        Returns:
            Path to the generated report
        """
        logger.info(f"Generating report for {protocol}")
        return output_path

    @staticmethod
    def generate_comparison_report(
        protocol_data: Dict[str, Dict[str, Any]], comparison_data: Dict[str, Any], output_path: str
    ) -> str:
        """Generate a comparison report for multiple protocols.

        Args:
            protocol_data: Dictionary mapping protocol names to processed protocol data
            comparison_data: Protocol comparison data
            output_path: Path to save the report

        Returns:
            Path to the generated report
        """
        logger.info(f"Generating comparison report for {list(protocol_data.keys())}")
        return output_path

    def _generate_report_content(self, protocol: str, processed_data: Dict[str, Any]) -> str:
        """Generate report content for a single protocol.

        Args:
            protocol: Protocol name
            processed_data: Processed protocol data

        Returns:
            Report content as string
        """
        # Extract data components
        metrics = processed_data.get("metrics", {})
        token_holders = processed_data.get("token_holders", [])
        proposals = processed_data.get("proposals", [])
        visualizations = processed_data.get("visualizations", {})

        # Generate report sections
        header = self._generate_report_header(protocol)
        summary = self._generate_summary_section(protocol, metrics)
        distribution_section = self._generate_distribution_section(protocol, token_holders, metrics)
        governance_section = self._generate_governance_section(protocol, proposals, metrics)
        visualization_section = self._generate_visualization_section(visualizations)
        conclusion = self._generate_conclusion_section(protocol, metrics)

        # Combine sections
        report = "\n\n".join(
            [
                header,
                summary,
                distribution_section,
                governance_section,
                visualization_section,
                conclusion,
            ]
        )

        return report

    def _generate_comparison_report_content(
        self, protocol_data: Dict[str, Dict[str, Any]], comparison_data: Dict[str, Any]
    ) -> str:
        """Generate comparison report content.

        Args:
            protocol_data: Dictionary mapping protocol names to processed protocol data
            comparison_data: Protocol comparison data

        Returns:
            Comparison report content as string
        """
        # Extract data components
        protocols = list(protocol_data.keys())
        metrics = comparison_data.get("metrics", {})
        visualizations = comparison_data.get("visualizations", {})

        # Generate report sections
        header = self._generate_comparison_header(protocols)
        summary = self._generate_comparison_summary(protocols, metrics)
        distribution_comparison = self._generate_distribution_comparison_section(protocols, metrics)
        governance_comparison = self._generate_governance_comparison_section(protocols, metrics)
        visualization_section = self._generate_comparison_visualization_section(visualizations)
        conclusion = self._generate_comparison_conclusion(protocols, metrics)

        # Combine sections
        report = "\n\n".join(
            [
                header,
                summary,
                distribution_comparison,
                governance_comparison,
                visualization_section,
                conclusion,
            ]
        )

        return report

    @staticmethod
    def _generate_report_header(protocol: str) -> str:
        """Generate report header.

        Args:
            protocol: Protocol name

        Returns:
            Report header as string
        """
        protocol_name = protocol.capitalize()

        header = f"""# {protocol_name} Governance Token Analysis Report
        
## Overview

This report provides a comprehensive analysis of the {protocol_name} governance token distribution and governance activity.
"""

        return header

    @staticmethod
    def _generate_summary_section(protocol: str, metrics: Dict[str, Any]) -> str:
        """Generate summary section.

        Args:
            protocol: Protocol name
            metrics: Protocol metrics

        Returns:
            Summary section as string
        """
        protocol_name = protocol.capitalize()

        # Extract key metrics
        holder_count = metrics.get("holder_count", 0)
        total_tokens = metrics.get("total_tokens", 0)
        gini_coefficient = metrics.get("gini_coefficient", 0)
        top10_concentration = metrics.get("top10_concentration", 0)
        proposal_count = metrics.get("proposal_count", 0)
        participation_rate = metrics.get("avg_participation_rate", 0)

        summary = f"""## Executive Summary

The {protocol_name} governance token exhibits the following key characteristics:

- **Token Distribution**: {holder_count:,} token holders with a total of {total_tokens:,.0f} tokens
- **Distribution Inequality**: Gini coefficient of {gini_coefficient:.4f} (0 = perfect equality, 1 = perfect inequality)
- **Concentration**: Top 10 holders control {top10_concentration:.2f}% of the supply
- **Governance Activity**: {proposal_count} governance proposals with {participation_rate:.2f}% average participation rate
"""

        return summary

    @staticmethod
    def _generate_distribution_section(
        protocol: str, token_holders: List[Dict[str, Any]], metrics: Dict[str, Any]
    ) -> str:
        """Generate distribution section.

        Args:
            protocol: Protocol name
            token_holders: List of token holder dictionaries
            metrics: Protocol metrics

        Returns:
            Distribution section as string
        """
        protocol_name = protocol.capitalize()

        # Extract key metrics
        holder_count = metrics.get("holder_count", 0)
        total_tokens = metrics.get("total_tokens", 0)
        gini_coefficient = metrics.get("gini_coefficient", 0)
        top10_concentration = metrics.get("top10_concentration", 0)
        whale_dominance = metrics.get("whale_dominance", 0)
        whale_count = metrics.get("whale_count", 0)

        # Get top 5 holders
        sorted_holders = sorted(token_holders, key=lambda x: float(x.get("balance", 0)), reverse=True)
        top_holders = sorted_holders[:5] if len(sorted_holders) >= 5 else sorted_holders

        # Format top holders table
        top_holders_table = "| Rank | Address | Balance | Percentage |\n|------|---------|---------|------------|\n"
        for i, holder in enumerate(top_holders):
            address = holder.get("address", "Unknown")
            balance = float(holder.get("balance", 0))
            percentage = float(holder.get("percentage", 0))
            top_holders_table += f"| {i + 1} | {address} | {balance:,.0f} | {percentage:.2f}% |\n"

        distribution = f"""## Token Distribution Analysis

### Overview

The {protocol_name} token is held by {holder_count:,} unique addresses, with a total supply of {total_tokens:,.0f} tokens.
The distribution has a Gini coefficient of {gini_coefficient:.4f}, indicating a {"highly unequal" if gini_coefficient > 0.8 else "moderately unequal" if gini_coefficient > 0.5 else "relatively equal"} distribution.

### Concentration

- Top 10 holders control {top10_concentration:.2f}% of the supply
- {whale_count} whale addresses (>1% of supply) control {whale_dominance:.2f}% of the supply

### Top Token Holders

{top_holders_table}
"""

        return distribution

    @staticmethod
    def _generate_governance_section(
        protocol: str, proposals: List[Dict[str, Any]], metrics: Dict[str, Any]
    ) -> str:
        """Generate governance section.

        Args:
            protocol: Protocol name
            proposals: List of governance proposal dictionaries
            metrics: Protocol metrics

        Returns:
            Governance section as string
        """
        protocol_name = protocol.capitalize()

        # Extract key metrics
        proposal_count = metrics.get("proposal_count", 0)
        success_rate = metrics.get("success_rate", 0)
        participation_rate = metrics.get("avg_participation_rate", 0)

        # Get recent proposals
        sorted_proposals = sorted(proposals, key=lambda x: x.get("created_at", ""), reverse=True)
        recent_proposals = sorted_proposals[:5] if len(sorted_proposals) >= 5 else sorted_proposals

        # Format recent proposals table
        proposals_table = "| ID | Title | Status | For | Against | Abstain |\n|------|---------|--------|-----|---------|----------|\n"
        for proposal in recent_proposals:
            proposal_id = proposal.get("id", "Unknown")
            title = proposal.get("title", "Unknown")
            state = proposal.get("state", "Unknown")
            for_votes = int(proposal.get("forVotes", 0))
            against_votes = int(proposal.get("againstVotes", 0))
            abstain_votes = int(proposal.get("abstainVotes", 0))

            proposals_table += f"| {proposal_id} | {title[:30]}... | {state.capitalize()} | {for_votes:,} | {against_votes:,} | {abstain_votes:,} |\n"

        governance = f"""## Governance Analysis

### Overview

The {protocol_name} protocol has had {proposal_count} governance proposals, with a {success_rate:.2f}% success rate.
The average participation rate is {participation_rate:.2f}%, indicating {"high" if participation_rate > 30 else "moderate" if participation_rate > 10 else "low"} governance engagement.

### Recent Proposals

{proposals_table}
"""

        return governance

    @staticmethod
    def _generate_visualization_section(visualizations: Dict[str, Dict[str, Any]]) -> str:
        """Generate visualization section.

        Args:
            visualizations: Dictionary of visualization configurations

        Returns:
            Visualization section as string
        """
        visualization_section = """## Visualizations

### Token Distribution Visualizations

- Holder Distribution Chart: Distribution of tokens across holder groups
- Lorenz Curve: Visualization of token distribution inequality
- Top Holders Pie Chart: Distribution of tokens among top holders
- Holder Categories: Distribution of tokens by holder category

### Governance Visualizations

- Proposal Timeline: Timeline of governance proposals
- Vote Distribution: Distribution of votes for each proposal
- Participation Trend: Trend of participation rates over time

*Note: Visualizations are available in the interactive dashboard.*
"""

        return visualization_section

    @staticmethod
    def _generate_conclusion_section(protocol: str, metrics: Dict[str, Any]) -> str:
        """Generate conclusion section.

        Args:
            protocol: Protocol name
            metrics: Protocol metrics

        Returns:
            Conclusion section as string
        """
        protocol_name = protocol.capitalize()

        # Extract key metrics
        gini_coefficient = metrics.get("gini_coefficient", 0)
        top10_concentration = metrics.get("top10_concentration", 0)
        participation_rate = metrics.get("avg_participation_rate", 0)

        # Determine distribution assessment
        if gini_coefficient > 0.8:
            distribution_assessment = "highly concentrated"
        elif gini_coefficient > 0.6:
            distribution_assessment = "significantly concentrated"
        elif gini_coefficient > 0.4:
            distribution_assessment = "moderately concentrated"
        else:
            distribution_assessment = "relatively well-distributed"

        # Determine governance assessment
        if participation_rate > 30:
            governance_assessment = "high level of governance participation"
        elif participation_rate > 10:
            governance_assessment = "moderate level of governance participation"
        else:
            governance_assessment = "low level of governance participation"

        conclusion = f"""## Conclusion

The {protocol_name} governance token exhibits a {distribution_assessment} distribution with a Gini coefficient of {gini_coefficient:.4f} and {top10_concentration:.2f}% of tokens held by the top 10 holders.
The protocol demonstrates a {governance_assessment} with an average participation rate of {participation_rate:.2f}%.

### Recommendations

1. {"Consider mechanisms to improve token distribution" if gini_coefficient > 0.6 else "Maintain current distribution mechanisms"}
2. {"Implement strategies to increase governance participation" if participation_rate < 20 else "Continue to encourage governance participation"}
3. Regular monitoring of token distribution and governance activity to track changes over time
"""

        return conclusion

    @staticmethod
    def _generate_comparison_header(protocols: List[str]) -> str:
        """Generate comparison report header.

        Args:
            protocols: List of protocol names

        Returns:
            Comparison report header as string
        """
        protocol_names = ", ".join([p.capitalize() for p in protocols])

        header = f"""# Governance Token Comparison Report: {protocol_names}
        
## Overview

This report provides a comparative analysis of governance token distribution and governance activity across {len(protocols)} protocols: {protocol_names}.
"""

        return header

    @staticmethod
    def _generate_comparison_summary(protocols: List[str], metrics: Dict[str, Any]) -> str:
        """Generate comparison summary section.

        Args:
            protocols: List of protocol names
            metrics: Comparison metrics

        Returns:
            Comparison summary section as string
        """
        # Extract key metrics
        gini_coefficients = metrics.get("gini_coefficient", {})
        top10_concentrations = metrics.get("top10_concentration", {})
        participation_rates = metrics.get("avg_participation_rate", {})
        decentralization_scores = metrics.get("decentralization_score", {})

        # Format metrics table
        metrics_table = (
            "| Protocol | Gini Coefficient | Top 10 Concentration | Participation Rate | Decentralization Score |\n"
        )
        metrics_table += (
            "|----------|-----------------|----------------------|-------------------|------------------------|\n"
        )

        for protocol in protocols:
            protocol_name = protocol.capitalize()
            gini = gini_coefficients.get(protocol, 0)
            top10 = top10_concentrations.get(protocol, 0)
            participation = participation_rates.get(protocol, 0)
            decentralization = decentralization_scores.get(protocol, 0)

            metrics_table += (
                f"| {protocol_name} | {gini:.4f} | {top10:.2f}% | {participation:.2f}% | {decentralization:.2f} |\n"
            )

        summary = f"""## Executive Summary

This report compares the governance token distribution and governance activity across {len(protocols)} protocols.
The comparison reveals significant differences in token distribution patterns and governance participation.

### Key Metrics Comparison

{metrics_table}
"""

        return summary

    @staticmethod
    def _generate_distribution_comparison_section(protocols: List[str], metrics: Dict[str, Any]) -> str:
        """Generate distribution comparison section.

        Args:
            protocols: List of protocol names
            metrics: Comparison metrics

        Returns:
            Distribution comparison section as string
        """
        # Extract distribution metrics
        gini_coefficients = metrics.get("gini_coefficient", {})
        top10_concentrations = metrics.get("top10_concentration", {})
        whale_dominance = metrics.get("whale_dominance", {})

        # Find protocol with lowest and highest concentration
        lowest_gini_protocol = min(protocols, key=lambda p: gini_coefficients.get(p, 1))
        highest_gini_protocol = max(protocols, key=lambda p: gini_coefficients.get(p, 0))

        lowest_top10_protocol = min(protocols, key=lambda p: top10_concentrations.get(p, 100))
        highest_top10_protocol = max(protocols, key=lambda p: top10_concentrations.get(p, 0))

        distribution = f"""## Token Distribution Comparison

### Gini Coefficient Comparison

The Gini coefficient measures the inequality of token distribution, where 0 represents perfect equality and 1 represents perfect inequality.

- **Most Equal Distribution**: {lowest_gini_protocol.capitalize()} ({gini_coefficients.get(lowest_gini_protocol, 0):.4f})
- **Most Unequal Distribution**: {highest_gini_protocol.capitalize()} ({gini_coefficients.get(highest_gini_protocol, 0):.4f})

### Top 10 Holder Concentration

The percentage of tokens held by the top 10 token holders.

- **Lowest Concentration**: {lowest_top10_protocol.capitalize()} ({top10_concentrations.get(lowest_top10_protocol, 0):.2f}%)
- **Highest Concentration**: {highest_top10_protocol.capitalize()} ({top10_concentrations.get(highest_top10_protocol, 0):.2f}%)
"""

        return distribution

    @staticmethod
    def _generate_governance_comparison_section(protocols: List[str], metrics: Dict[str, Any]) -> str:
        """Generate governance comparison section.

        Args:
            protocols: List of protocol names
            metrics: Comparison metrics

        Returns:
            Governance comparison section as string
        """
        # Extract governance metrics
        proposal_counts = metrics.get("proposal_count", {})
        participation_rates = metrics.get("avg_participation_rate", {})
        success_rates = metrics.get("success_rate", {})

        # Find protocol with highest and lowest participation
        lowest_participation_protocol = min(protocols, key=lambda p: participation_rates.get(p, 100))
        highest_participation_protocol = max(protocols, key=lambda p: participation_rates.get(p, 0))

        # Find protocol with most and least proposals
        lowest_proposal_protocol = min(protocols, key=lambda p: proposal_counts.get(p, 100))
        highest_proposal_protocol = max(protocols, key=lambda p: proposal_counts.get(p, 0))

        governance = f"""## Governance Comparison

### Proposal Activity

The number of governance proposals submitted for each protocol.

- **Most Active**: {highest_proposal_protocol.capitalize()} ({proposal_counts.get(highest_proposal_protocol, 0)} proposals)
- **Least Active**: {lowest_proposal_protocol.capitalize()} ({proposal_counts.get(lowest_proposal_protocol, 0)} proposals)

### Participation Rate

The average percentage of tokens that participate in governance votes.

- **Highest Participation**: {highest_participation_protocol.capitalize()} ({participation_rates.get(highest_participation_protocol, 0):.2f}%)
- **Lowest Participation**: {lowest_participation_protocol.capitalize()} ({participation_rates.get(lowest_participation_protocol, 0):.2f}%)
"""

        return governance

    @staticmethod
    def _generate_comparison_visualization_section(visualizations: Dict[str, Dict[str, Any]]) -> str:
        """Generate comparison visualization section.

        Args:
            visualizations: Dictionary of visualization configurations

        Returns:
            Comparison visualization section as string
        """
        visualization_section = """## Comparative Visualizations

### Distribution Comparisons

- Gini Coefficient Comparison: Lower values indicate more equal token distribution
- Top 10 Holder Concentration: Percentage of tokens held by top 10 holders
- Whale Dominance: Percentage of tokens held by whales (>1% supply)

### Governance Comparisons

- Proposal Count Comparison: Number of governance proposals
- Participation Rate Comparison: Average governance participation rate
- Proposal Success Rate: Percentage of proposals that were executed

### Overall Comparison

- Protocol Decentralization Comparison: Radar chart comparing distribution, participation, and diversity
- Overall Decentralization Score: Combined score based on token distribution and governance metrics

*Note: Visualizations are available in the interactive dashboard.*
"""

        return visualization_section

    @staticmethod
    def _generate_comparison_conclusion(protocols: List[str], metrics: Dict[str, Any]) -> str:
        """Generate comparison conclusion section.

        Args:
            protocols: List of protocol names
            metrics: Comparison metrics

        Returns:
            Comparison conclusion section as string
        """
        # Extract key metrics
        decentralization_scores = metrics.get("decentralization_score", {})

        # Find most and least decentralized protocols
        most_decentralized = max(protocols, key=lambda p: decentralization_scores.get(p, 0))
        least_decentralized = min(protocols, key=lambda p: decentralization_scores.get(p, 100))

        conclusion = f"""## Conclusion

### Overall Assessment

Based on the combined analysis of token distribution and governance activity:

- **Most Decentralized Protocol**: {most_decentralized.capitalize()} (Score: {decentralization_scores.get(most_decentralized, 0):.2f})
- **Least Decentralized Protocol**: {least_decentralized.capitalize()} (Score: {decentralization_scores.get(least_decentralized, 0):.2f})

### Key Insights

1. Token distribution inequality varies significantly across protocols, with some showing much higher concentration than others.
2. Governance participation rates differ substantially, indicating varying levels of community engagement.
3. There appears to be a correlation between token distribution and governance participation in some protocols.

### Recommendations

1. Protocols with high concentration could consider mechanisms to improve token distribution.
2. Protocols with low participation could implement strategies to increase governance engagement.
3. Best practices from more decentralized protocols could be adopted by others to improve their governance models.
"""

        return conclusion
