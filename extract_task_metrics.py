#!/usr/bin/env python3
"""
Script to extract task metrics from study_summary.json files and create CSV files.
"""

import json
import os
import pandas as pd
import glob
from pathlib import Path
import re


def extract_task_id_from_task_name(task_name):
    """
    Extract task ID from the full task name.
    E.g., from "2025-07-19_19-27-58_GenericAgent-gpt-4.1-2025-04-14_on_webmall.Webmall_Best_Fit_Specific_Task6_20"
    extract "Webmall_Best_Fit_Specific_Task6"
    """
    # Find the pattern that matches task types followed by numbers
    pattern = r"(Webmall_[A-Za-z_]+_Task\d+)"
    match = re.search(pattern, task_name)
    if match:
        return match.group(1)

    # Fallback: try to extract from task_type if the above doesn't work
    # This shouldn't normally happen based on the data structure we saw
    return None


def process_study_summary_file(json_file_path):
    """
    Process a single study_summary.json file and extract task metrics.

    Returns:
        pd.DataFrame: DataFrame with extracted task metrics
    """
    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)

        # List to store all task records
        task_records = []

        # Iterate through each task type in by_task_type
        by_task_type = data.get("by_task_type", {})

        for category, task_type_data in by_task_type.items():
            tasks = task_type_data.get("tasks", [])

            for task in tasks:
                # Extract task_id from the full task name
                task_name = task.get("task", "")
                task_id = extract_task_id_from_task_name(task_name)

                if task_id is None:
                    # Fallback: use task_type from the task data
                    task_type_from_task = task.get("task_type", category)
                    print(
                        f"Warning: Could not extract task_id from '{task_name}', using task_type: {task_type_from_task}"
                    )
                    task_id = task_type_from_task

                # Clean up category name by removing "_Task" suffix if present
                clean_category = (
                    category.rstrip("_Task") if category.endswith("_Task") else category
                )

                # Create record
                record = {
                    "category": clean_category,
                    "task_id": task_id,
                    "task_completion_rate": task.get("task_completion", 0.0),
                    "precision": task.get("precision", 0.0),
                    "recall": task.get("recall", 0.0),
                    "f1_score": task.get("f1_score", 0.0),
                    "input_tokens": task.get("input_tokens", 0),
                    "output_tokens": task.get("output_tokens", 0),
                }

                task_records.append(record)

        # Create DataFrame
        df = pd.DataFrame(task_records)

        return df

    except Exception as e:
        print(f"Error processing file {json_file_path}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error


def main():
    """
    Main function to process all study_summary.json files and create CSV outputs.
    """
    # Find all study_summary.json files in the study_results directory
    base_path = "/Users/david/VSCode/WebMallSeminar/AgentLab/study_results"
    json_files = glob.glob(
        os.path.join(base_path, "**/study_summary.json"), recursive=True
    )

    # Create output directory for CSV files
    csv_output_base_path = "/Users/david/VSCode/WebMallSeminar/study_results_csv"
    os.makedirs(csv_output_base_path, exist_ok=True)

    print(f"Found {len(json_files)} study_summary.json files:")
    for file_path in json_files:
        print(f"  - {file_path}")

    print(f"\nCSV files will be saved to: {csv_output_base_path}")

    # Process each file
    for json_file_path in json_files:
        print(f"\nProcessing: {json_file_path}")

        # Extract the study directory name for output filename
        study_dir = os.path.dirname(json_file_path)
        study_name = os.path.basename(study_dir)

        # Process the file
        df = process_study_summary_file(json_file_path)

        if not df.empty:
            # Define output CSV path in the separate CSV directory
            csv_output_path = os.path.join(
                csv_output_base_path, f"{study_name}_task_metrics.csv"
            )

            # Write to CSV
            df.to_csv(csv_output_path, index=False)
            print(f"  Saved {len(df)} task records to: {csv_output_path}")

            # Print summary
            print(f"  Categories found: {df['category'].unique().tolist()}")
            print(f"  Total tasks: {len(df)}")
        else:
            print(f"  No data extracted from {json_file_path}")

    print("\nScript completed successfully!")


if __name__ == "__main__":
    main()
