#!/usr/bin/env python
"""
Script to convert historical metrics data from the old format to the new format.

The new format is a list of data points, each containing a complete snapshot
of metrics for a specific timestamp.
"""

import json
import os
from datetime import datetime


def convert_historical_data(token, input_file, output_file=None):
    """
    Convert historical data from old format to new format.

    Args:
        token: Token symbol (e.g., 'COMP', 'UNI')
        input_file: Path to input file in old format
        output_file: Path to output file in new format (defaults to same as input)
    """
    # Load the old format data
    with open(input_file, "r") as f:
        old_data = json.load(f)

    # Create the new format data
    new_data = {"token": token, "data_points": []}

    # Convert each data point
    for i, date in enumerate(old_data["dates"]):
        # Create a data point with the complete set of metrics
        data_point = {
            "token": token,
            "contract_address": old_data.get("contract_address", f"0x{i:040x}"),
            "timestamp": f"{date}T00:00:00Z",
            "metrics": {
                "gini_coefficient": old_data["gini_coefficient"][i],
                "herfindahl_index": old_data["herfindahl_index"][i],
                "concentration": {
                    "top_5_pct": old_data["top_5_pct"][i],
                    "top_10_pct": old_data["top_10_pct"][i],
                    "top_20_pct": old_data["top_20_pct"][i],
                    "top_50_pct": old_data.get(
                        "top_50_pct", [0] * len(old_data["dates"])
                    )[i],
                },
            },
        }

        new_data["data_points"].append(data_point)

    # Save the new format data
    if output_file is None:
        output_file = input_file

    with open(output_file, "w") as f:
        json.dump(new_data, f, indent=2)

    print(f"Converted {len(new_data['data_points'])} data points for {token} token")
    return new_data


def main():
    """Convert historical data for all tokens."""
    # Define paths
    data_dir = "data/historical"

    # Convert UNI data
    uni_input = os.path.join(data_dir, "uni_historical_metrics.json")
    if os.path.exists(uni_input):
        convert_historical_data("UNI", uni_input)

    # Convert COMP data
    comp_input = os.path.join(data_dir, "comp_historical_metrics.json")
    if os.path.exists(comp_input):
        convert_historical_data("COMP", comp_input)

    print("Conversion complete!")


if __name__ == "__main__":
    main()
