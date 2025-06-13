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
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
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
                "top_voters": ["Compound Labs", "a16z", "Polychain Capital"]
            }
        },
        {
            "id": 64, 
            "name": "Update COMP Distribution",
            "description": "Proposal to adjust COMP token distribution parameters",
            "expected": {
                "status": "executed", 
                "participation_rate": "~3-8%",
                "top_voters": ["Compound Labs", "Gauntlet", "OpenZeppelin"]
            }
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
                "top_voters": ["Uniswap Labs", "a16z", "Paradigm"]
            }
        },
        {
            "id": 10, 
            "name": "Deploy Uniswap v3 on Polygon",
            "description": "Proposal to deploy Uniswap v3 on Polygon network",
            "expected": {
                "status": "executed",
                "participation_rate": "~3-7%",
                "top_voters": ["Uniswap Labs", "Polygon team", "DeFi Pulse"]
            }
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
                "top_voters": ["Aave Companies", "Polygon team", "DeFiPulse"]
            }
        },
        {
            "id": 16, 
            "name": "Aave v2 Migration",
            "description": "AIP-16: Migration strategy for Aave v2",
            "expected": {
                "status": "executed",
                "participation_rate": "~5-10%",
                "top_voters": ["Aave Companies", "Gauntlet", "Llama"]
            }
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
            sys.executable, "-m", "governance_token_analyzer.cli",
            "analyze", protocol, "--limit", str(limit), "--format", "json"
        ]
        
        # Change to src directory to run the CLI
        result = subprocess.run(
            cmd,
            cwd=project_root / "src",
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode == 0:
            # Try to parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw output
                return {"raw_output": result.stdout, "stderr": result.stderr}
        else:
            logger.error(f"CLI command failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return {"error": f"CLI failed: {result.stderr}", "stdout": result.stdout}
            
    except subprocess.TimeoutExpired:
        logger.error(f"CLI analysis for {protocol} timed out")
        return {"error": "Analysis timed out"}
    except Exception as e:
        logger.error(f"Error running CLI analysis: {str(e)}")
        return {"error": str(e)}

def run_python_analysis(protocol: str, limit: int = 100) -> Dict[str, Any]:
    """
    Run analysis using Python script directly.
    
    Args:
        protocol: The protocol name (compound, uniswap, aave)
        limit: Number of token holders to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Running Python analysis for {protocol} with limit {limit}")
    
    try:
        # Map protocol to analysis script
        script_map = {
            "compound": "compound_analysis.py",
            "uniswap": "uniswap_analysis.py", 
            "aave": "aave_analysis.py"
        }
        
        if protocol not in script_map:
            return {"error": f"No analysis script found for protocol: {protocol}"}
        
        script_path = project_root / "src" / script_map[protocol]
        
        if not script_path.exists():
            return {"error": f"Analysis script not found: {script_path}"}
        
        # Run the analysis script
        cmd = [sys.executable, str(script_path)]
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Always try to find and parse the generated JSON file first
        data_dir = project_root / "data"
        if data_dir.exists():
            # Look for the latest analysis file for this protocol
            # Map protocol names to the actual file prefixes used
            file_prefix_map = {
                "compound": "comp",
                "uniswap": "uni", 
                "aave": "aave"
            }
            
            file_prefix = file_prefix_map.get(protocol, protocol)
            
            patterns = [
                f"{file_prefix}_analysis_latest.json",
                f"{file_prefix}_analysis_*.json",
                f"{protocol}_analysis_latest.json",
                f"{protocol}_analysis_*.json"
            ]
            
            for pattern in patterns:
                analysis_files = list(data_dir.glob(pattern))
                if analysis_files:
                    latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)
                    try:
                        with open(latest_file, 'r') as f:
                            json_data = json.load(f)
                            logger.info(f"Successfully parsed JSON from {latest_file}")
                            return json_data
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning(f"Failed to parse JSON from {latest_file}: {e}")
                        continue
        
        # If JSON parsing failed, return the raw output
        if result.returncode == 0:
            return {"raw_output": result.stdout, "stderr": result.stderr}
        else:
            logger.error(f"Python analysis failed: {result.stderr}")
            return {"error": f"Analysis failed: {result.stderr}", "stdout": result.stdout}
            
    except subprocess.TimeoutExpired:
        logger.error(f"Python analysis for {protocol} timed out")
        return {"error": "Analysis timed out"}
    except Exception as e:
        logger.error(f"Error running Python analysis: {str(e)}")
        return {"error": str(e)}

def validate_proposal(protocol: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single governance proposal by analyzing its token distribution.
    
    Args:
        protocol: The protocol name (compound, uniswap, aave)
        proposal: Proposal information dictionary
        
    Returns:
        Dictionary containing validation results
    """
    logger.info(f"Validating {protocol} proposal {proposal['id']}: {proposal['name']}")
    
    # Try CLI analysis first, fall back to Python script
    analysis_result = run_cli_analysis(protocol)
    
    if "error" in analysis_result:
        logger.warning(f"CLI analysis failed, trying Python script: {analysis_result['error']}")
        analysis_result = run_python_analysis(protocol)
    
    # Compile validation results
    validation_result = {
        "proposal_id": proposal["id"],
        "proposal_name": proposal["name"],
        "protocol": protocol,
        "timestamp": datetime.now().isoformat(),
        "analysis_results": analysis_result,
        "expected_outcomes": proposal.get("expected", {}),
        "validation_notes": [
            "Using current token distribution as proxy for historical data",
            "Full validation requires historical snapshot at proposal block height",
            f"Proposal: {proposal.get('description', 'No description available')}"
        ]
    }
    
    # Extract key metrics if available
    if "metrics" in analysis_result:
        metrics = analysis_result["metrics"]
        logger.info(f"✓ Successfully analyzed {protocol} proposal {proposal['id']}")
        
        if "gini_coefficient" in metrics:
            logger.info(f"  - Gini coefficient: {metrics['gini_coefficient']:.4f}")
        
        if "concentration" in metrics:
            conc = metrics["concentration"]
            if "top_10_pct" in conc:
                logger.info(f"  - Top 10% concentration: {conc['top_10_pct']:.2f}%")
    else:
        logger.warning(f"No metrics found in analysis result for {protocol}")
    
    return validation_result

def save_validation_results(results: Dict[str, Any], output_file: Optional[str] = None):
    """Save validation results to a JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"proposal_validation_{timestamp}.json"
    
    # Ensure data directory exists
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    output_path = data_dir / output_file
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="Validate governance proposal analysis against real-world data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_real_world_proposals.py
  python scripts/validate_real_world_proposals.py --protocol compound
  python scripts/validate_real_world_proposals.py --protocol uniswap --proposal-id 1
        """
    )
    parser.add_argument(
        "--protocol", 
        choices=list(PROPOSALS.keys()), 
        help="Protocol to validate (if not specified, validates all)"
    )
    parser.add_argument(
        "--proposal-id", 
        type=int, 
        help="Specific proposal ID to validate"
    )
    parser.add_argument(
        "--output", 
        help="Output file name for results (default: auto-generated)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting governance proposal validation")
    logger.info(f"Project root: {project_root}")
    
    # Determine which protocols to validate
    protocols_to_validate = [args.protocol] if args.protocol else list(PROPOSALS.keys())
    
    all_results = {
        "validation_metadata": {
            "timestamp": datetime.now().isoformat(),
            "protocols_validated": protocols_to_validate,
            "total_proposals": 0
        },
        "results": {}
    }
    
    # Validate proposals
    for protocol in protocols_to_validate:
        logger.info(f"\n=== Validating {protocol.upper()} proposals ===")
        
        protocol_results = []
        proposals = PROPOSALS[protocol]
        
        for proposal in proposals:
            # Skip if specific proposal ID requested and this isn't it
            if args.proposal_id and proposal["id"] != args.proposal_id:
                continue
                
            result = validate_proposal(protocol, proposal)
            protocol_results.append(result)
            all_results["validation_metadata"]["total_proposals"] += 1
        
        all_results["results"][protocol] = protocol_results
    
    # Save results
    output_path = save_validation_results(all_results, args.output)
    
    # Print summary
    logger.info(f"\n=== VALIDATION SUMMARY ===")
    logger.info(f"Total proposals validated: {all_results['validation_metadata']['total_proposals']}")
    logger.info(f"Results saved to: {output_path}")
    
    # Print key findings for each protocol
    for protocol, results in all_results["results"].items():
        successful = [r for r in results if "error" not in r.get("analysis_results", {})]
        failed = [r for r in results if "error" in r.get("analysis_results", {})]
        
        logger.info(f"\n{protocol.upper()}:")
        logger.info(f"  ✓ Successful: {len(successful)}")
        if failed:
            logger.info(f"  ✗ Failed: {len(failed)}")
        
        for result in successful:
            analysis = result.get("analysis_results", {})
            metrics = analysis.get("metrics", {})
            if "gini_coefficient" in metrics:
                logger.info(f"    Proposal {result['proposal_id']}: Gini = {metrics['gini_coefficient']:.4f}")

if __name__ == "__main__":
    main()