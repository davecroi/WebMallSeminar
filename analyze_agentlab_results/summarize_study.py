from .task_logs_extractor import summarize_single_task
import os
import json
import re
import csv
from collections import defaultdict

STUDY_RESULTS_DIR = "../AgentLab/study_results"

def extract_task_type(subdir_name):
    try:
        task_part = subdir_name.split('.')[-1]
        match = re.match(r"^(.*?_Task)\d+(?:_\d+){0,2}$", task_part)
        return match.group(1) if match else "Unknown_Task"
    except Exception:
        return "Unknown_Task"

def read_goal_achievement_data(subdir):
    """Read goal achievement data from goal_achievement.csv"""
    goal_achievement_path = os.path.join(subdir, "goal_achievement.csv")
    goals_data = {
        'answer_goals': {'total': 0, 'achieved': 0},
        'checkpoint_goals': {'total': 0, 'achieved': 0},
    }
    
    if os.path.exists(goal_achievement_path):
        try:
            with open(goal_achievement_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    goal_desc = row.get('goal_description', '')
                    achieved = row.get('achieved', '').lower() == 'true'
                    
                    if 'answer' in goal_desc.lower():
                        goals_data['answer_goals']['total'] += 1
                        if achieved:
                            goals_data['answer_goals']['achieved'] += 1
                    else:
                        goals_data['checkpoint_goals']['total'] += 1
                        if achieved:
                            goals_data['checkpoint_goals']['achieved'] += 1
            
            return goals_data
        except Exception as e:
            print(f"⚠️ Error reading goal_achievement.csv in {subdir}: {e}")
    
    return goals_data

def read_penalties_data(subdir):
    """Read penalties data from penalties.csv"""
    penalties_path = os.path.join(subdir, "penalties.csv")
    penalty_data = {'penalty': 0.0, 'wrong_solutions': []}
    
    if os.path.exists(penalties_path):
        try:
            with open(penalties_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    penalty_data['penalty'] = float(row.get('penalty', 0))
                    wrong_solutions_str = row.get('wrong_solutions', '')
                    if wrong_solutions_str:
                        penalty_data['wrong_solutions'] = wrong_solutions_str.split('|')
            
            return penalty_data
        except Exception as e:
            print(f"⚠️ Error reading penalties.csv in {subdir}: {e}")
    
    return penalty_data

def read_summary_info_data(subdir):
    """Read token and cost data from summary_info.json"""
    summary_info_path = os.path.join(subdir, "summary_info.json")
    summary_info_data = {
        'input_tokens': 0,
        'output_tokens': 0,
        'cost': 0.0
    }
    
    if os.path.exists(summary_info_path):
        try:
            with open(summary_info_path, 'r') as f:
                data = json.load(f)
                summary_info_data['input_tokens'] = data.get('stats.cum_input_tokens', 0)
                summary_info_data['output_tokens'] = data.get('stats.cum_output_tokens', 0)
                summary_info_data['cost'] = data.get('stats.cum_cost', 0.0)
            
            return summary_info_data
        except Exception as e:
            print(f"⚠️ Error reading summary_info.json in {subdir}: {e}")
    
    return summary_info_data

def summarize_all_tasks_in_subdirs(root_directory):
    task_results = []

    for subdir, dirs, files in os.walk(root_directory):
        if any(f.startswith("step_") and f.endswith(".pkl.gz") for f in files):
            print(f"📁 Summarizing task in: {subdir}")
            summarize_single_task(subdir)

            task_summary_path = os.path.join(subdir, "task_summary.json")
            subdir_name = os.path.basename(subdir)

            # Collect goal and penalty data
            goal_data = read_goal_achievement_data(subdir)
            penalty_data = read_penalties_data(subdir)
            summary_info_data = read_summary_info_data(subdir)
            
            # Calculate task completion metrics
            task_completed = False
            partial_completion = 0.0
            checkpoint_completion = 0.0
            
            if goal_data['answer_goals']['total'] > 0:
                partial_completion = goal_data['answer_goals']['achieved'] / goal_data['answer_goals']['total']
                task_completed = goal_data['answer_goals']['achieved'] == goal_data['answer_goals']['total']  # All answer goals achieved
            
            if goal_data['checkpoint_goals']['total'] > 0:
                checkpoint_completion = goal_data['checkpoint_goals']['achieved'] / goal_data['checkpoint_goals']['total']
            
            task_result = {
                "task": subdir_name,
                "task_type": extract_task_type(subdir_name),
                "critical_error": False,
                "num_action_errors": 0,
                "cumulative_reward": 0.0,
                "task_completed": task_completed,
                "partial_completion": partial_completion,
                "checkpoint_completion": checkpoint_completion,
                "penalty": penalty_data['penalty'],
                "terminated": False,
                "truncated": False,
                "num_steps": 0,
                "input_tokens": summary_info_data['input_tokens'],
                "output_tokens": summary_info_data['output_tokens'],
                "cost": summary_info_data['cost']
            }

            if os.path.exists(task_summary_path):
                try:
                    with open(task_summary_path, "r") as f:
                        task_data = json.load(f)

                    steps = task_data["steps"] if isinstance(task_data, dict) and "steps" in task_data else task_data
                    sorted_keys = sorted(steps.keys(), key=lambda x: int(x))
                    
                    # Count the number of steps
                    task_result["num_steps"] = len(sorted_keys)
                    
                    if sorted_keys:
                        last_step_data = steps[sorted_keys[-1]]
                        if last_step_data.get("err_msg") and last_step_data.get("stack_trace"):
                            task_result["critical_error"] = True
                        
                        # Track terminated/truncated status from the last step
                        if last_step_data.get("finished") == "terminated":
                            task_result["terminated"] = True
                        elif last_step_data.get("finished") == "truncated":
                            task_result["truncated"] = True

                    for step in steps.values():
                        if "action_error" in step:
                            task_result["num_action_errors"] += 1
                        if "cumulative_reward" in step:
                            task_result["cumulative_reward"] = step["cumulative_reward"]

                except Exception as e:
                    print(f"⚠️ Could not process task_summary.json in {subdir}: {e}")

            task_results.append(task_result)

    # ------------------- AGGREGATE BY TASK TYPE -----------------------
    type_summary = {}
    full_summary = {}

    for result in task_results:
        task_type = result["task_type"]
        subtype_match = re.search(r"(Task\d+)", result["task"])
        subtype = subtype_match.group(1) if subtype_match else "Unknown"

        if task_type not in type_summary:
            type_summary[task_type] = {
                "count": 0,
                "subtypes": set(),
                "critical_errors": 0,
                "action_errors": 0,
                "cumulative_rewards": 0.0,
                "completed_tasks": 0,
                "partial_completion_sum": 0.0,
                "checkpoint_completion_sum": 0.0,
                "terminated_count": 0,
                "truncated_count": 0,
                "total_steps": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0
            }
            full_summary[task_type] = {
                "summary": {},
                "tasks": []
            }

        ts = type_summary[task_type]
        ts["count"] += 1
        ts["subtypes"].add(subtype)
        ts["critical_errors"] += int(result["critical_error"])
        ts["action_errors"] += result["num_action_errors"]
        ts["cumulative_rewards"] += result["cumulative_reward"]
        ts["completed_tasks"] += int(result["task_completed"])
        ts["partial_completion_sum"] += result["partial_completion"]
        ts["checkpoint_completion_sum"] += result["checkpoint_completion"]
        ts["terminated_count"] += int(result["terminated"])
        ts["truncated_count"] += int(result["truncated"])
        ts["total_steps"] += result["num_steps"]
        ts["total_input_tokens"] += result["input_tokens"]
        ts["total_output_tokens"] += result["output_tokens"]
        ts["total_cost"] += result["cost"]

        full_summary[task_type]["tasks"].append(result)

    # ------------------- PRINT PER-TASK-TYPE STATS -------------------
    print("\n📊 Task-Type Summary:\n")
    export_type_summary = {}

    for task_type in sorted(type_summary.keys()):
        ts = type_summary[task_type]
        count = ts["count"]
        subtype_count = len(ts["subtypes"])
        avg_critical = ts["critical_errors"] / count
        avg_action = ts["action_errors"] / count
        avg_reward = ts["cumulative_rewards"] / count
        task_completion_rate = ts["completed_tasks"] / count
        avg_partial_completion = ts["partial_completion_sum"] / count
        avg_checkpoint_completion = ts["checkpoint_completion_sum"] / count
        terminated_rate = ts["terminated_count"] / count
        truncated_rate = ts["truncated_count"] / count
        avg_steps = ts["total_steps"] / count
        avg_input_tokens = ts["total_input_tokens"] / count
        avg_output_tokens = ts["total_output_tokens"] / count
        avg_cost = ts["total_cost"] / count

        print(f"🔧 {task_type}  ({subtype_count} subtypes, {count} total runs)")
        print(f"   ❗ Avg Critical Errors: {avg_critical:.2f}")
        print(f"   ⚠️  Avg Action Errors: {avg_action:.2f}")
        print(f"   🎯 Avg Cumulative Reward: {avg_reward:.2f}")
        print(f"   ✅ Task Completion Rate: {task_completion_rate:.2f}")
        print(f"   📊 Avg Partial Completion: {avg_partial_completion:.2f}")
        print(f"   🔄 Avg Checkpoint Completion: {avg_checkpoint_completion:.2f}")
        print(f"   🏁 Terminated Rate: {terminated_rate:.2f}")
        print(f"   ⏱️ Truncated Rate: {truncated_rate:.2f}")
        print(f"   🔢 Avg Steps: {avg_steps:.2f}")
        print(f"   📥 Avg Input Tokens: {avg_input_tokens:.0f}")
        print(f"   📤 Avg Output Tokens: {avg_output_tokens:.0f}")
        print(f"   💰 Avg Cost: ${avg_cost:.4f}\n")

        # Store clean summary
        export_type_summary[task_type] = {
            "num_subtypes": subtype_count,
            "num_runs": count,
            "avg_critical_errors": avg_critical,
            "avg_action_errors": avg_action,
            "avg_cumulative_reward": avg_reward,
            "task_completion_rate": task_completion_rate,
            "avg_partial_completion": avg_partial_completion,
            "avg_checkpoint_completion": avg_checkpoint_completion,
            "terminated_rate": terminated_rate,
            "truncated_rate": truncated_rate,
            "avg_steps": avg_steps,
            "avg_input_tokens": avg_input_tokens,
            "avg_output_tokens": avg_output_tokens,
            "avg_cost": avg_cost
        }

        # Attach to full summary
        full_summary[task_type]["summary"] = export_type_summary[task_type]

    # ------------------- PRINT INDIVIDUAL TASK DETAILS -------------------
    critical_tasks = sorted([t for t in task_results if t["critical_error"]], key=lambda x: x["task"])
    non_critical_tasks = sorted([t for t in task_results if not t["critical_error"]], key=lambda x: x["task"])

    def print_task_summary(tasks, header=None):
        if tasks and header:
            print(header)
        for result in tasks:
            print(f"🧾 Task: {result['task']}")
            if result["num_action_errors"] > 0:
                print(f"   ⚠️  Action Errors: {result['num_action_errors']}")
            print(f"   🎯 Cumulative Reward: {result['cumulative_reward']}")
            print(f"   ✅ Task Completed: {result['task_completed']}")
            print(f"   📊 Partial Completion: {result['partial_completion']:.2f}")
            print(f"   🔄 Checkpoint Completion: {result['checkpoint_completion']:.2f}")
            print(f"   💲 Penalty: {result['penalty']}")
            print(f"   🔢 Steps: {result['num_steps']}")
            print(f"   📥 Input Tokens: {result['input_tokens']}")
            print(f"   📤 Output Tokens: {result['output_tokens']}")
            print(f"   💰 Cost: ${result['cost']:.4f}")
            if result["terminated"]:
                print(f"   🏁 Terminated: Yes")
            if result["truncated"]:
                print(f"   ⏱️ Truncated: Yes")
            print()

    print("📄 Individual Task Results:\n")

    if critical_tasks:
        print_task_summary(critical_tasks, header="❗ Tasks with Critical Errors:\n")

    print_task_summary(non_critical_tasks, header="✅ Tasks without Critical Errors:\n" if critical_tasks else None)

    # ------------------- EXPORT TO JSON FILES -------------------
    json_path_summary = os.path.join(root_directory, "study_summary_short.json")
    json_path_full = os.path.join(root_directory, "study_summary.json")

    with open(json_path_summary, "w") as f:
        json.dump(export_type_summary, f, indent=2)

    with open(json_path_full, "w") as f:
        json.dump(full_summary, f, indent=2)

    print(f"📦 JSON output saved to:\n  - {json_path_summary}\n  - {json_path_full}")

if __name__ == "__main__":
    # Get all study directories in the results folder
    if not os.path.exists(STUDY_RESULTS_DIR):
        print(f"❌ Study results directory not found: {STUDY_RESULTS_DIR}")
        exit(1)
    
    study_dirs = [d for d in os.listdir(STUDY_RESULTS_DIR) 
                  if os.path.isdir(os.path.join(STUDY_RESULTS_DIR, d))]
    
    if not study_dirs:
        print(f"❌ No study directories found in: {STUDY_RESULTS_DIR}")
        exit(1)
    
    print(f"🔍 Found {len(study_dirs)} study directories:")
    for study_dir in sorted(study_dirs):
        print(f"  - {study_dir}")
    print()
    
    # Process each study directory
    for study_dir in sorted(study_dirs):
        study_path = os.path.join(STUDY_RESULTS_DIR, study_dir)
        print(f"🚀 Processing study: {study_dir}")
        print(f"📁 Path: {study_path}")
        print("-" * 80)
        
        try:
            summarize_all_tasks_in_subdirs(study_path)
            print(f"✅ Completed processing: {study_dir}\n")
        except Exception as e:
            print(f"❌ Error processing {study_dir}: {e}\n")
        
        print("=" * 80)
        print()
