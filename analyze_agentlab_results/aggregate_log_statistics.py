#!/usr/bin/env python3

import os
import re
import csv
import pandas as pd
from collections import defaultdict
import argparse

def normalize_action(action_input):
    """Extract the base action name from a full action string. Returns None if not a valid action format."""
    if pd.isna(action_input): # Handle NaN first
        return None
    
    action_str = str(action_input).strip() # Convert to string and strip whitespace
    
    if not action_str or action_str.lower() == 'none': # Handle empty or "None" strings
        return None
        
    # Only accept verbs followed by '(' to identify real actions
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', action_str)
    if match:
        return match.group(1) # Return the matched group (the action verb)
        
    return None # If no match (e.g., starts with number, or is not an action verb format)

def process_log_file(file_path):
    """Process a single task_stepwise_log.csv file and return action counts by shop."""
    try:
        df = pd.read_csv(file_path, sep='\t')
        
        # Make sure required columns exist
        if 'shop_id' not in df.columns or 'action' not in df.columns:
            print(f"Warning: Missing required columns in {file_path}")
            return {}
        
        # Initialize counter dictionary
        shop_action_counts = defaultdict(lambda: defaultdict(int))
        
        # Process each row
        for _, row in df.iterrows():
            action_input = row['action'] # Get the raw action value
            
            normalized_action = normalize_action(action_input) # Normalize it
            
            # If normalize_action returns None, it means it's not a valid/countable action
            if normalized_action is None:
                continue
                
            shop_id_val = row['shop_id']
            if pd.isna(shop_id_val):
                shop_id_str = 'none'
            else:
                shop_id_str = str(shop_id_val)
                
            # Increment counter
            shop_action_counts[shop_id_str][normalized_action] += 1
            
        return shop_action_counts
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return {}

def aggregate_statistics(study_dir):
    """
    Aggregate action statistics from all task_stepwise_log.csv files in a study directory.
    
    Args:
        study_dir (str): Path to the study directory
        
    Returns:
        dict: Aggregated action counts by shop
    """
    # Counter for all actions by shop
    all_shop_actions = defaultdict(lambda: defaultdict(int))
    all_actions = set()
    all_shops = set()
    
    # Walk through the directory and find all task_stepwise_log.csv files
    log_files = []
    for root, _, files in os.walk(study_dir):
        for file in files:
            if file == 'task_stepwise_log.csv':
                log_files.append(os.path.join(root, file))
    
    # Process each log file
    for log_file in log_files:
        shop_action_counts = process_log_file(log_file)
        
        # Merge counts
        for shop, actions in shop_action_counts.items():
            all_shops.add(shop)
            for action, count in actions.items():
                all_actions.add(action)
                all_shop_actions[shop][action] += count
    
    return all_shop_actions, sorted(all_shops), sorted(all_actions)

def save_results_to_csv(shop_action_counts, all_shops, all_actions, output_path):
    """Save the aggregated results to a CSV file."""
    # all_actions should be clean by now due to changes in normalize_action and process_log_file
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        # Ensure all_actions is a list of unique, sorted strings
        header = ['shop_id'] + sorted(list(set(all_actions))) 
        writer.writerow(header)
        
        # Write data for each shop
        for shop in all_shops: # all_shops should already be sorted as per aggregate_statistics
            row_data = [shop]
            for action_name in header[1:]: # Iterate through the sorted action names in the header
                row_data.append(shop_action_counts[shop].get(action_name, 0)) # Use .get for safety, though keys should exist
            writer.writerow(row_data)

def process_study_directory(study_dir):
    """Process a single study directory and save results to it."""
    print(f"Processing study directory: {study_dir}")
    
    # Define output path within the study directory
    output_path = os.path.join(study_dir, 'action_statistics.csv')
    
    # Aggregate statistics
    shop_action_counts, all_shops, all_actions = aggregate_statistics(study_dir)
    
    if not all_shops or not all_actions:
        print(f"No valid data found in log files for study: {os.path.basename(study_dir)}")
        return False
    
    # Save results
    save_results_to_csv(shop_action_counts, all_shops, all_actions, output_path)
    print(f"Results saved to {output_path}")
    return True

def main():
    # Base directory containing all study results
    base_dir = "../AgentLab/study_results"
    
    if not os.path.isdir(base_dir):
        print(f"Error: Base directory {base_dir} does not exist")
        return 1
    
    # Find all subdirectories in the base directory
    study_dirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) 
                  if os.path.isdir(os.path.join(base_dir, d))]
    
    if not study_dirs:
        print(f"No study directories found in {base_dir}")
        return 1
    
    # Process each study directory
    successful = 0
    for study_dir in study_dirs:
        if process_study_directory(study_dir):
            successful += 1
    
    print(f"Completed processing {successful} out of {len(study_dirs)} study directories")
    return 0

if __name__ == "__main__":
    exit(main())