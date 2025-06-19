"""Protocol Client for Governance Token Distribution Analyzer.

This module provides protocol-specific API client functionality for
interacting with governance protocols like Compound, Uniswap, and Aave.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base_client import GOVERNANCE_ADDRESSES, PROTOCOL_INFO, GOVERNANCE_QUERIES, VOTE_QUERIES

# Configure logging
logger = logging.getLogger(__name__)


class ProtocolClient:
    """Client for interacting with protocol-specific APIs."""

    def __init__(self, parent_client=None):
        """Initialize the Protocol client.

        Args:
            parent_client: Parent APIClient instance
        """
        self.parent_client = parent_client
        self.graph_api_key = parent_client.graph_api_key if parent_client else ""
        self.graph_clients = parent_client.graph_clients if parent_client else {}

    def get_proposal_data(self, protocol: str, limit: int = 10, use_real_data: bool = False) -> List[Dict[str, Any]]:
        """Get governance proposal data for a protocol.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            limit: Maximum number of proposals to return
            use_real_data: Whether to use real data or simulated data

        Returns:
            List of governance proposal dictionaries
        """
        if protocol.lower() not in GOVERNANCE_ADDRESSES:
            raise ValueError(f"Unsupported protocol: {protocol}")

        if use_real_data:
            return self._fetch_governance_proposals(protocol, limit)
        else:
            return self._generate_sample_proposal_data(protocol, limit)

    def get_votes_data(self, protocol: str, proposal_id: int, use_real_data: bool = False) -> List[Dict[str, Any]]:
        """Get governance votes data for a proposal.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            proposal_id: ID of the proposal to get votes for
            use_real_data: Whether to use real data or simulated data

        Returns:
            List of vote dictionaries
        """
        if protocol.lower() not in GOVERNANCE_ADDRESSES:
            raise ValueError(f"Unsupported protocol: {protocol}")

        if use_real_data:
            return self._fetch_governance_votes(protocol, proposal_id)
        else:
            return self._generate_sample_vote_data(protocol, proposal_id)

    def _fetch_governance_proposals(self, protocol: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch governance proposals from The Graph API.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            limit: Maximum number of proposals to return

        Returns:
            List of governance proposal dictionaries
        """
        if protocol.lower() not in self.graph_clients:
            logger.warning(f"No Graph client available for {protocol}")
            return self._generate_sample_proposal_data(protocol, limit)

        graph_client = self.graph_clients[protocol.lower()]
        query = GOVERNANCE_QUERIES.get(protocol.lower(), "")

        if not query:
            logger.warning(f"No GraphQL query defined for {protocol}")
            return self._generate_sample_proposal_data(protocol, limit)

        try:
            # Batch fetch proposals
            batch_size = 100
            all_proposals = []

            for offset in range(0, limit, batch_size):
                variables = {
                    "first": min(batch_size, limit - offset),
                    "skip": offset,
                }

                response = graph_client.execute_query(query, variables)

                if "data" in response and "proposals" in response["data"]:
                    proposals = response["data"]["proposals"]
                    all_proposals.extend(proposals)

                    # Break if we have enough proposals
                    if len(all_proposals) >= limit:
                        break
                else:
                    logger.warning(f"Invalid response from The Graph API for {protocol}")
                    break

            # Fetch votes for each proposal
            for proposal in all_proposals:
                proposal_id = proposal.get("id")
                if proposal_id:
                    votes = self._fetch_governance_votes(protocol, proposal_id)
                    proposal["votes"] = votes

            return all_proposals[:limit]
        except Exception as e:
            logger.error(f"Error fetching governance proposals for {protocol}: {e}")
            return self._generate_sample_proposal_data(protocol, limit)

    def _fetch_governance_votes(self, protocol: str, proposal_id: int) -> List[Dict[str, Any]]:
        """Fetch governance votes from The Graph API.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            proposal_id: ID of the proposal to get votes for

        Returns:
            List of vote dictionaries
        """
        if protocol.lower() not in self.graph_clients:
            logger.warning(f"No Graph client available for {protocol}")
            return self._generate_sample_vote_data(protocol, proposal_id)

        graph_client = self.graph_clients[protocol.lower()]
        query = VOTE_QUERIES.get(protocol.lower(), "")

        if not query:
            logger.warning(f"No GraphQL query defined for {protocol}")
            return self._generate_sample_vote_data(protocol, proposal_id)

        try:
            variables = {
                "proposalId": str(proposal_id),
            }

            response = graph_client.execute_query(query, variables)

            if "data" in response and "votes" in response["data"]:
                votes = response["data"]["votes"]
                return votes
            else:
                logger.warning(f"Invalid response from The Graph API for {protocol} votes")
                return self._generate_sample_vote_data(protocol, proposal_id)
        except Exception as e:
            logger.error(f"Error fetching governance votes for {protocol} proposal {proposal_id}: {e}")
            return self._generate_sample_vote_data(protocol, proposal_id)

    def _generate_sample_proposal_data(self, protocol: str, count: int) -> List[Dict[str, Any]]:
        """Generate sample governance proposal data.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            count: Number of proposals to generate

        Returns:
            List of simulated governance proposal dictionaries
        """
        if protocol.lower() not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")

        protocol_info = PROTOCOL_INFO[protocol.lower()]

        # Sample proposal titles and descriptions for each protocol
        proposal_templates = {
            "compound": [
                {
                    "title": "Adjust the reserve factor for {asset}",
                    "description": "This proposal adjusts the reserve factor for {asset} from {old_value}% to {new_value}%.",
                },
                {
                    "title": "Add support for {asset}",
                    "description": "This proposal adds support for {asset} with the following parameters: Collateral factor: {cf}%, Reserve factor: {rf}%, Supply cap: {cap}.",
                },
                {
                    "title": "Update {asset} risk parameters",
                    "description": "This proposal updates the risk parameters for {asset}. New collateral factor: {cf}%, New reserve factor: {rf}%, New supply cap: {cap}.",
                },
                {
                    "title": "Upgrade Comptroller implementation",
                    "description": "This proposal upgrades the Comptroller implementation to address {issue} and add {feature}.",
                },
                {
                    "title": "Distribute COMP to {recipient}",
                    "description": "This proposal distributes {amount} COMP to {recipient} for {reason}.",
                },
            ],
            "uniswap": [
                {
                    "title": "Deploy Uniswap v3 on {chain}",
                    "description": "This proposal deploys Uniswap v3 on {chain} with the following parameters: {params}.",
                },
                {
                    "title": "Adjust fee tier for {pair}",
                    "description": "This proposal adjusts the fee tier for {pair} from {old_fee}% to {new_fee}%.",
                },
                {
                    "title": "Add new fee tier of {fee}%",
                    "description": "This proposal adds a new fee tier of {fee}% for pairs with {characteristic} characteristics.",
                },
                {
                    "title": "Allocate UNI for {program}",
                    "description": "This proposal allocates {amount} UNI for the {program} program over the next {duration} months.",
                },
                {
                    "title": "Update price oracle for {pair}",
                    "description": "This proposal updates the price oracle for {pair} to use {oracle} with {method}.",
                },
            ],
            "aave": [
                {
                    "title": "Add {asset} as collateral",
                    "description": "This proposal adds {asset} as collateral with the following parameters: LTV: {ltv}%, Liquidation threshold: {lt}%, Liquidation bonus: {lb}%.",
                },
                {
                    "title": "Update interest rate strategy for {asset}",
                    "description": "This proposal updates the interest rate strategy for {asset} with the following parameters: Base: {base}%, Slope1: {slope1}%, Slope2: {slope2}%, Optimal utilization: {util}%.",
                },
                {
                    "title": "Enable borrowing for {asset}",
                    "description": "This proposal enables borrowing for {asset} with the following parameters: {params}.",
                },
                {
                    "title": "Deploy Aave v3 on {chain}",
                    "description": "This proposal deploys Aave v3 on {chain} with the following parameters: {params}.",
                },
                {
                    "title": "Allocate {amount} AAVE to {recipient}",
                    "description": "This proposal allocates {amount} AAVE to {recipient} for {reason}.",
                },
            ],
        }

        # Assets for each protocol
        assets = {
            "compound": ["USDC", "ETH", "DAI", "WBTC", "LINK", "UNI", "COMP"],
            "uniswap": ["ETH/USDC", "ETH/DAI", "WBTC/ETH", "UNI/ETH", "USDC/DAI"],
            "aave": ["USDC", "ETH", "DAI", "WBTC", "LINK", "UNI", "AAVE"],
        }

        # Chains
        chains = ["Arbitrum", "Optimism", "Polygon", "Base", "zkSync Era", "Avalanche"]

        # Generate proposals
        proposals = []
        for i in range(count):
            # Select template
            templates = proposal_templates.get(protocol.lower(), proposal_templates["compound"])
            template = random.choice(templates)

            # Fill in template variables
            title = template["title"]
            description = template["description"]

            # Replace placeholders
            if "{asset}" in title or "{asset}" in description:
                asset = random.choice(assets.get(protocol.lower(), assets["compound"]))
                title = title.replace("{asset}", asset)
                description = description.replace("{asset}", asset)

            if "{pair}" in title or "{pair}" in description:
                pair = random.choice(assets.get("uniswap", assets["compound"]))
                title = title.replace("{pair}", pair)
                description = description.replace("{pair}", pair)

            if "{chain}" in title or "{chain}" in description:
                chain = random.choice(chains)
                title = title.replace("{chain}", chain)
                description = description.replace("{chain}", chain)

            if "{amount}" in title or "{amount}" in description:
                amount = f"{random.randint(10000, 1000000):,}"
                title = title.replace("{amount}", amount)
                description = description.replace("{amount}", amount)

            if "{recipient}" in title or "{recipient}" in description:
                recipient = f"0x{random.randint(0, 0xFFFFFFFF):08x}"
                title = title.replace("{recipient}", recipient)
                description = description.replace("{recipient}", recipient)

            if "{reason}" in description:
                reasons = [
                    "community development",
                    "grants program",
                    "protocol improvements",
                    "security audits",
                    "bug bounties",
                ]
                reason = random.choice(reasons)
                description = description.replace("{reason}", reason)

            if "{old_value}" in description and "{new_value}" in description:
                old_value = random.randint(5, 20)
                new_value = random.randint(5, 20)
                while new_value == old_value:
                    new_value = random.randint(5, 20)
                description = description.replace("{old_value}", str(old_value))
                description = description.replace("{new_value}", str(new_value))

            if "{cf}" in description:
                cf = random.randint(50, 85)
                description = description.replace("{cf}", str(cf))

            if "{rf}" in description:
                rf = random.randint(5, 25)
                description = description.replace("{rf}", str(rf))

            if "{cap}" in description:
                cap = f"{random.randint(1, 100):,}M"
                description = description.replace("{cap}", cap)

            if "{issue}" in description:
                issues = ["gas optimization", "security vulnerability", "accounting error", "protocol efficiency"]
                issue = random.choice(issues)
                description = description.replace("{issue}", issue)

            if "{feature}" in description:
                features = [
                    "improved liquidation mechanism",
                    "better interest rate model",
                    "new risk management features",
                    "enhanced governance",
                ]
                feature = random.choice(features)
                description = description.replace("{feature}", feature)

            if "{old_fee}" in description and "{new_fee}" in description:
                old_fee = random.choice([0.05, 0.1, 0.3, 1.0])
                new_fee = random.choice([0.01, 0.05, 0.1, 0.3, 1.0])
                while new_fee == old_fee:
                    new_fee = random.choice([0.01, 0.05, 0.1, 0.3, 1.0])
                description = description.replace("{old_fee}", str(old_fee))
                description = description.replace("{new_fee}", str(new_fee))

            if "{fee}" in description:
                fee = random.choice([0.01, 0.05, 0.1, 0.3, 1.0])
                description = description.replace("{fee}", str(fee))

            if "{characteristic}" in description:
                characteristics = ["high volatility", "stable coin", "low liquidity", "high volume"]
                characteristic = random.choice(characteristics)
                description = description.replace("{characteristic}", characteristic)

            if "{program}" in description:
                programs = ["liquidity mining", "developer grants", "ecosystem fund", "education"]
                program = random.choice(programs)
                description = description.replace("{program}", program)

            if "{duration}" in description:
                duration = random.randint(3, 24)
                description = description.replace("{duration}", str(duration))

            if "{oracle}" in description:
                oracles = ["Chainlink", "Uniswap TWAP", "Band Protocol", "API3"]
                oracle = random.choice(oracles)
                description = description.replace("{oracle}", oracle)

            if "{method}" in description:
                methods = ["time-weighted average", "volume-weighted average", "exponential moving average"]
                method = random.choice(methods)
                description = description.replace("{method}", method)

            if "{ltv}" in description:
                ltv = random.randint(50, 85)
                description = description.replace("{ltv}", str(ltv))

            if "{lt}" in description:
                lt = random.randint(60, 90)
                description = description.replace("{lt}", str(lt))

            if "{lb}" in description:
                lb = random.randint(5, 15)
                description = description.replace("{lb}", str(lb))

            if "{base}" in description:
                base = random.randint(0, 5)
                description = description.replace("{base}", str(base))

            if "{slope1}" in description:
                slope1 = random.randint(5, 15)
                description = description.replace("{slope1}", str(slope1))

            if "{slope2}" in description:
                slope2 = random.randint(50, 150)
                description = description.replace("{slope2}", str(slope2))

            if "{util}" in description:
                util = random.randint(70, 90)
                description = description.replace("{util}", str(util))

            if "{params}" in description:
                params = "standard protocol parameters"
                description = description.replace("{params}", params)

            # Generate random vote counts
            for_votes = random.randint(100000, 1000000)
            against_votes = random.randint(10000, for_votes)
            abstain_votes = random.randint(1000, 100000)

            # Generate timestamps
            end_date = datetime.now() - timedelta(days=random.randint(1, 365))
            start_date = end_date - timedelta(days=random.randint(3, 7))
            created_date = start_date - timedelta(days=random.randint(1, 3))

            # Generate proposal
            proposal = {
                "id": str(count - i),  # Newest proposals first
                "title": title,
                "description": description,
                "proposer": f"0x{random.randint(0, 0xFFFFFFFF):08x}",
                "targets": [f"0x{random.randint(0, 0xFFFFFFFF):08x}"],
                "values": ["0"],
                "signatures": [f"function{random.randint(1, 5)}(address,uint256)"],
                "calldatas": [f"0x{random.randint(0, 0xFFFFFFFF):08x}"],
                "startBlock": random.randint(10000000, 15000000),
                "endBlock": random.randint(15000001, 20000000),
                "forVotes": str(for_votes),
                "againstVotes": str(against_votes),
                "abstainVotes": str(abstain_votes),
                "canceled": False,
                "queued": random.random() > 0.1,
                "executed": random.random() > 0.2,
                "eta": int((end_date + timedelta(days=2)).timestamp()),
                "createdAt": int(created_date.timestamp()),
                "updatedAt": int(end_date.timestamp()),
                "votes": self._generate_sample_vote_data(protocol, count - i),
            }

            proposals.append(proposal)

        return proposals

    def _generate_sample_vote_data(self, protocol: str, proposal_id: int) -> List[Dict[str, Any]]:
        """Generate sample governance vote data.

        Args:
            protocol: Protocol name (compound, uniswap, aave)
            proposal_id: ID of the proposal to generate votes for

        Returns:
            List of simulated vote dictionaries
        """
        if protocol.lower() not in PROTOCOL_INFO:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Number of votes to generate
        vote_count = random.randint(50, 200)

        # Generate votes
        votes = []
        for i in range(vote_count):
            # Generate random voter address
            voter = f"0x{random.randint(0, 0xFFFFFFFF):08x}"

            # Generate random vote weight
            voting_power = random.randint(1, 1000000)

            # Generate random vote support
            # 0 = against, 1 = for, 2 = abstain
            support = random.choices([0, 1, 2], weights=[0.3, 0.6, 0.1])[0]

            # Generate random reason
            reasons = [
                "I support this proposal because it improves the protocol.",
                "This proposal is not in the best interest of the protocol.",
                "I'm voting against this proposal due to security concerns.",
                "I'm abstaining because I need more information.",
                "This is a good step forward for the protocol.",
                "I have concerns about the implementation details.",
                "",  # Empty reason
            ]
            reason = random.choice(reasons) if random.random() > 0.5 else ""

            # Generate random block number and timestamp
            block_number = random.randint(10000000, 20000000)
            block_timestamp = int((datetime.now() - timedelta(days=random.randint(1, 30))).timestamp())

            # Generate vote
            vote = {
                "id": f"{proposal_id}-{voter}",
                "voter": voter,
                "support": support,
                "votingPower": str(voting_power),
                "reason": reason,
                "blockNumber": str(block_number),
                "blockTimestamp": str(block_timestamp),
                "transactionHash": f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFF):016x}",
            }

            votes.append(vote)

        # Sort by voting power
        votes = sorted(votes, key=lambda x: int(x["votingPower"]), reverse=True)

        return votes
