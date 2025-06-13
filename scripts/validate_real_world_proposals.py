"""
Validate the analysis engine against real-world governance proposals.
Usage:
    python scripts/validate_real_world_proposals.py [--protocol compound|uniswap|aave] [--proposal-id ID]
"""

import argparse
import logging
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure logs directory exists
logs_dir = project_root / ".logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(logs_dir / "validation.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Define proposals to validate with known historical data
PROPOSALS = {
    "compound": [
        {
            "id": 32,
            "name": "Add COMP as Collateral Asset",
            "description": "Proposal to add COMP token as collateral in Compound protocol",
            "expected": {
                "status": "executed",
                "participation_rate": "~5-10%",  # Typical for Compound proposals
                "top_voters": ["Compound Labs", "a16z", "Polychain Capital"],
            },
        },
        {
            "id": 64,
            "name": "Update COMP Distribution",
            "description": "Proposal to adjust COMP token distribution parameters",
            "expected": {
                "status": "executed",
                "participation_rate": "~3-8%",
                "top_voters": ["Compound Labs", "Gauntlet", "OpenZeppelin"],
            },
        },
    ],
    "uniswap": [
        {
            "id": 1,
            "name": "Uniswap Grants Program",
            "description": "First major governance proposal for UNI grants program",
            "expected": {
                "status": "executed",
                "participation_rate": "~2-5%",  # Lower participation typical for early proposals
                "top_voters": ["Uniswap Labs", "a16z", "Paradigm"],
            },
        },
        {
            "id": 10,
            "name": "Deploy Uniswap v3 on Polygon",
            "description": "Proposal to deploy Uniswap v3 on Polygon network",
            "expected": {
                "status": "executed",
                "participation_rate": "~3-7%",
                "top_voters": ["Uniswap Labs", "Polygon team", "DeFi Pulse"],
            },
        },
    ],
    "aave": [
        {
            "id": 1,
            "name": "Launch Aave on Polygon",
            "description": "AIP-1: Deploy Aave protocol on Polygon network",
            "expected": {
                "status": "executed",
                "participation_rate": "~4-8%",
                "top_voters": ["Aave Companies", "Polygon team", "DeFiPulse"],
            },
        },
        {
            "id": 16,
            "name": "Aave v2 Migration",
            "description": "AIP-16: Migration strategy for Aave v2",
            "expected": {
                "status": "executed",
                "participation_rate": "~5-10%",
                "top_voters": ["Aave Companies", "Gauntlet", "Llama"],
            },
        },
    ],
}


def run_cli_analysis(protocol: str, limit: int = 100) -> Dict[str, Any]:
    """
    Run the governance token analyzer CLI to analyze a protocol.

    Args:
        protocol: The protocol name (compound, uniswap, aave)
        limit: Number of token holders to analyze

    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Running CLI analysis for {protocol} with limit {limit}")

    try:
        # Use the CLI to analyze the token
        cmd = [
            sys.executable,
            "-m",
            "governance_token_analyzer.cli",
            "analyze",
            protocol,
            "--limit",
            str(limit),
            "--format",
            "json",
        ]

        # Change to src directory to run the CLI
        result = subprocess.run(
            cmd,
            cwd=project_root / "src",
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )

        if result.returncode == 0:
            # Try to parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON output from CLI: {e}")
                return {"error": f"JSON parse error: {e}", "raw_output": result.stdout}
        else:
            logger.error(f"CLI command failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return {"error": f"CLI failed: {result.stderr}", "stdout": result.stdout}

    except subprocess.TimeoutExpired:
        logger.error(f"CLI analysis for {protocol} timed out")
        return {"error": "Analysis timed out"}
    except Exception as exception:
        logger.error(f"Error running CLI analysis: {str(exception)}")
        return {"error": str(exception)}


def run_python_analysis(protocol: str, limit: int = 100, data_dir: str = "data") -> Dict[str, Any]:
    """
    Run analysis using Python script directly.

    Args:
        protocol: The protocol name (compound, uniswap, aave)
        limit: Number of token holders to analyze
        data_dir: Directory to read/write proposal data

    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Running Python analysis for {protocol} with limit {limit}")

    try:
        # Try to execute the protocol-specific script if available
        script_result = _execute_protocol_script(protocol, project_root)
        if script_result:
            return script_result
        
        # If script execution failed or script doesn't exist, look for analysis files
        return _find_analysis_files(protocol, data_dir)
        
    except Exception as exception:
        logger.error(f"Error running Python analysis: {str(exception)}")
        return {"error": str(exception)}


def _execute_protocol_script(protocol: str, project_root: Path) -> Dict[str, Any]:
    """
    Execute a protocol-specific analysis script.

    Args:
        protocol: The protocol name
        project_root: Path to the project root directory

    Returns:
        Dictionary containing analysis results or None if script doesn't exist/fails
    """
    # Map protocol to analysis script
    script_map = {
        "compound": "compound_analysis.py",
        "uniswap": "uniswap_analysis.py",
        "aave": "aave_analysis.py",
    }

    if protocol not in script_map:
        return None

    script_path = project_root / "src" / script_map[protocol]

    if not script_path.exists():
        return None

    try:
        # Run the analysis script
        cmd = [sys.executable, str(script_path)]

        result = subprocess.run(
            cmd, cwd=project_root, capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            logger.warning(f"Script execution failed with code {result.returncode}")
            return None

        return {"script_execution": "success", "stdout": result.stdout}
    except Exception as e:
        logger.warning(f"Failed to execute script: {e}")
        return None


def _find_analysis_files(protocol: str, data_dir: str) -> Dict[str, Any]:
    """
    Find and parse analysis files for a protocol.

    Args:
        protocol: The protocol name
        data_dir: Directory to search for analysis files

    Returns:
        Dictionary containing analysis results
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        return {"error": f"Data directory not found: {data_dir}"}

    # Map protocol names to the actual file prefixes used
    file_prefix_map = {"compound": "comp", "uniswap": "uni", "aave": "aave"}
    file_prefix = file_prefix_map.get(protocol, protocol)

    patterns = [
        f"{file_prefix}_analysis_latest.json",
        f"{file_prefix}_analysis_*.json",
        f"{protocol}_analysis_latest.json",
        f"{protocol}_analysis_*.json",
    ]

    for pattern in patterns:
        analysis_files = list(data_path.glob(pattern))
        if analysis_files:
            latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest_file, "r") as f:
                    json_data = json.load(f)
                    logger.info(f"Successfully parsed JSON from {latest_file}")
                    return json_data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to parse JSON from {latest_file}: {e}")
                continue

    return {"error": f"No valid analysis files found for {protocol}"}


def validate_proposal(protocol: str, proposal_id: int) -> Dict[str, Any]:
    """
    Validate a specific governance proposal.

    Args:
        protocol: The protocol name (compound, uniswap, aave)
        proposal_id: The ID of the proposal to validate

    Returns:
        Dictionary containing validation results
    """
    logger.info(f"Validating {protocol} proposal #{proposal_id}")

    # Find the proposal in our test data
    proposal_data = None
    for proposal in PROPOSALS.get(protocol, []):
        if proposal["id"] == proposal_id:
            proposal_data = proposal
            break

    if not proposal_data:
        return {
            "error": f"No test data found for {protocol} proposal #{proposal_id}",
            "available_proposals": [p["id"] for p in PROPOSALS.get(protocol, [])],
        }

    # Run analysis
    analysis_result = run_python_analysis(protocol)

    # Check if analysis was successful
    if "error" in analysis_result:
        return {
            "error": f"Analysis failed: {analysis_result['error']}",
            "proposal": proposal_data,
        }

    # Extract proposal-specific data from analysis
    proposal_analysis = {}
    if "proposals" in analysis_result:
        for p in analysis_result["proposals"]:
            if p.get("id") == proposal_id:
                proposal_analysis = p
                break

    # Compare expected vs actual results
    validation_result = {
        "protocol": protocol,
        "proposal_id": proposal_id,
        "proposal_name": proposal_data["name"],
        "expected": proposal_data["expected"],
        "analysis": proposal_analysis,
        "matches": {},
        "timestamp": datetime.now().isoformat(),
    }

    # Check status match
    if proposal_analysis.get("status"):
        expected_status = proposal_data["expected"]["status"]
        actual_status = proposal_analysis["status"]
        validation_result["matches"]["status"] = expected_status.lower() == actual_status.lower()

    # Check participation rate
    if proposal_analysis.get("participation_rate"):
        # Extract numeric range from expected rate (e.g., "~5-10%" -> (5, 10))
        expected_range = proposal_data["expected"]["participation_rate"]
        if "~" in expected_range and "-" in expected_range and "%" in expected_range:
            try:
                range_str = expected_range.replace("~", "").replace("%", "")
                min_rate, max_rate = map(float, range_str.split("-"))
                actual_rate = float(proposal_analysis["participation_rate"].replace("%", ""))
                validation_result["matches"]["participation_rate"] = min_rate <= actual_rate <= max_rate
            except (ValueError, AttributeError):
                validation_result["matches"]["participation_rate"] = False
        else:
            validation_result["matches"]["participation_rate"] = False

    # Check top voters
    if proposal_analysis.get("top_voters"):
        expected_voters = set(v.lower() for v in proposal_data["expected"]["top_voters"])
        actual_voters = set(v["name"].lower() for v in proposal_analysis["top_voters"][:5] if "name" in v)
        common_voters = expected_voters.intersection(actual_voters)
        validation_result["matches"]["top_voters"] = len(common_voters) >= 1  # At least one match

    # Overall validation success
    validation_result["success"] = all(validation_result["matches"].values()) if validation_result["matches"] else False

    return validation_result


def main():
    """Main function to run validation."""
    parser = argparse.ArgumentParser(description="Validate governance token analysis against real-world proposals")
    parser.add_argument("--protocol", choices=["compound", "uniswap", "aave"], help="Protocol to validate")
    parser.add_argument("--proposal-id", type=int, help="Specific proposal ID to validate")
    parser.add_argument("--all", action="store_true", help="Validate all protocols and proposals")
    args = parser.parse_args()

    if args.all:
        results = {}
        for protocol, proposals in PROPOSALS.items():
            protocol_results = {}
            for proposal in proposals:
                proposal_id = proposal["id"]
                result = validate_proposal(protocol, proposal_id)
                protocol_results[proposal_id] = result
            results[protocol] = protocol_results

        # Save results
        output_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"All validation results saved to {output_file}")

        # Print summary
        success_count = 0
        total_count = 0
        for protocol, protocol_results in results.items():
            for proposal_id, result in protocol_results.items():
                total_count += 1
                if result.get("success", False):
                    success_count += 1
        logger.info(f"Validation success rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    elif args.protocol and args.proposal_id:
        result = validate_proposal(args.protocol, args.proposal_id)
        logger.info(f"Validation result: {'SUCCESS' if result.get('success', False) else 'FAILURE'}")
        logger.info(f"Details: {result}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
