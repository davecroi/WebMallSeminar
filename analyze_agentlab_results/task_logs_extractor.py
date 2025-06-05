import os
import gzip
import pickle
import json
import re
from collections import defaultdict, OrderedDict
from glob import glob
from urllib.parse import urlparse

SHOP_PORT_DICT = {
    8085: "start page",
    8081: "shop1",
    8082: "shop2",
    8083: "shop3",
    8084: "shop4"
}

SHOP_DOMAIN_DICT = {
    "webmall-0.informatik.uni-mannheim.de": "start page",
    "webmall-1.informatik.uni-mannheim.de": "shop1",
    "webmall-2.informatik.uni-mannheim.de": "shop2",
    "webmall-3.informatik.uni-mannheim.de": "shop3",
    "webmall-4.informatik.uni-mannheim.de": "shop4"
}

def extract_step_number(filename):
    # This will match the 'step' followed by numbers like step1, step10, etc.
    match = re.search(r'step_(\d+)', filename)
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"Filename {filename} does not contain a valid step number.")

def extract_eco_metrics(agent_info):
    try:
        eco_logits = agent_info.get("extra_info", {}).get("eco_logits", {})
        metrics = {}
        for section in ["usage", "embodied"]:
            section_data = eco_logits.get(section, {})
            for key in ["energy", "gwp", "adpe", "pe"]:
                data = section_data.get(key, {})
                metric_key = f"{section}_{key}"
                metrics[metric_key] = {
                    "min": data.get("value", {}).get("min", 0),
                    "max": data.get("value", {}).get("max", 0),
                    "unit": data.get("unit", "")
                }
        return metrics
    except Exception as e:
        print(f"Error extracting metrics: {e}")
        return {}


def extract_task_summary(step_data):
    try:
        action = getattr(step_data, "action", "")
        url = step_data.obs.get("url", "") if hasattr(step_data, "obs") else ""
        think = step_data.agent_info.get("think", "") if hasattr(step_data, "agent_info") else ""

        task_summary = {
            "action": action,
            "url": url,
            "think": think
        }

        if step_data.terminated:
            task_summary["finished"] = 'terminated'
            return task_summary
        elif step_data.truncated:
            task_summary["finished"] = 'truncated'
            return task_summary

        # Match ax_tree element from action
        match = re.match(r".+\(\s*'(\d+)'\s*(?:,.*)?\)", action)
        if match:
            target_id = match.group(1)
            nodes = step_data.obs.get("axtree_object", {}).get("nodes", [])
            for node in nodes:
                if str(node.get("browsergym_id", "")) == target_id:
                    name = node.get("name", {}).get("value", "")
                    role = node.get("role", {}).get("value", "")
                    task_summary["axtree_object_info"] = f"axtree_object: {role}: {name}"
                    break

        return task_summary
    except Exception as e:
        print(f"Error extracting task summary: {e}")
        return {}


def summarize_single_task(directory="."):
    step_files = sorted(glob(os.path.join(directory, "step_*.pkl.gz")), key=extract_step_number)

    all_steps_data = {}
    all_task_summary = {}
    cumulative = defaultdict(lambda: {"min": 0, "max": 0, "unit": ""})
    cumulative_reward = 0.0
    previous_step_num = None
    step_nums_in_order = []
    last_step_data = None  # Store the last step data for extracting checklist

    for filepath in step_files:
        try:
            with gzip.open(filepath, "rb") as f:
                step_data = pickle.load(f)
                last_step_data = step_data  # Keep track of the last step

            step_num = step_data.step
            step_nums_in_order.append(step_num)

            # Eco metrics
            metrics = extract_eco_metrics(step_data.agent_info)
            all_steps_data[step_num] = metrics
            for key, val in metrics.items():
                cumulative[key]["min"] += val["min"]
                cumulative[key]["max"] += val["max"]
                cumulative[key]["unit"] = val["unit"]

            # Task summary (without reward or cumulative reward yet)
            task_summary = extract_task_summary(step_data)

            # Assign reward + error to previous step and update cumulative_reward
            if previous_step_num is not None:
                reward = step_data.reward
                cumulative_reward += reward
                all_task_summary[previous_step_num]["reward"] = reward
                all_task_summary[previous_step_num]["cumulative_reward"] = cumulative_reward

                last_action_error = step_data.obs.get("last_action_error")
                if last_action_error:
                    all_task_summary[previous_step_num]["action_error"] = last_action_error

            # Store current step summary
            all_task_summary[step_num] = task_summary
            previous_step_num = step_num

        except Exception as e:
            print(f"Failed to process {filepath}: {e}")


    csv_data_all = []

    for i in range(len(all_task_summary)):
        task_summary = all_task_summary.get(i)
        
        # Try to get shop_id by domain first, then fall back to port
        url = task_summary.get("url", "")
        parsed_url = urlparse(url)
        
        shop_id = "none"
        if parsed_url.hostname and parsed_url.hostname in SHOP_DOMAIN_DICT:
            shop_id = SHOP_DOMAIN_DICT[parsed_url.hostname]
        elif parsed_url.port and parsed_url.port in SHOP_PORT_DICT:
            shop_id = SHOP_PORT_DICT[parsed_url.port]
        
        action = task_summary.get("action")
        try:
            used_axtree_object = task_summary.get("axtree_object_info").replace("axtree_object: ", "")
        except AttributeError:
            used_axtree_object = "none"
        url = task_summary.get("url")
        reward = task_summary.get("reward")
        cumulative_reward = task_summary.get("cumulative_reward")
        thought = task_summary.get("think")
        experiment_id = os.path.basename(directory).split('/')[-1].split('.')[0]
        task_id = os.path.basename(directory).split('/')[-1].split('.')[1]

        csv_data_cur = [i, shop_id, action, used_axtree_object, url, reward, cumulative_reward, thought, experiment_id, task_id]
        csv_data_all.append(csv_data_cur)

    # Attach error from summary_info.json to the last step if available
    summary_info_path = os.path.join(directory, "summary_info.json")
    if os.path.exists(summary_info_path) and step_nums_in_order:
        try:
            with open(summary_info_path, "r") as f:
                summary_info = json.load(f)

            err_msg = summary_info.get("err_msg")
            stack_trace = summary_info.get("stack_trace")

            if err_msg or stack_trace:
                last_step = step_nums_in_order[-1]
                if err_msg:
                    all_task_summary[last_step]["err_msg"] = err_msg
                if stack_trace:
                    all_task_summary[last_step]["stack_trace"] = stack_trace
        except Exception as e:
            print(f"⚠️ Failed to read or parse summary_info.json: {e}")

    # Extract and save checklist data from the last step
    if last_step_data and hasattr(last_step_data, "task_info") and 'checklist' in last_step_data.task_info:
        checklist = last_step_data.task_info['checklist']
        checklist_data = []
        
        # Extract experiment and task ID for identification
        experiment_id = os.path.basename(directory).split('/')[-1].split('.')[0]
        task_id = os.path.basename(directory).split('/')[-1].split('.')[1]
        
        # Extract penalty and wrong solutions for separate penalties.csv
        penalty = last_step_data.task_info.get('penalty')
        wrong_solutions = last_step_data.task_info.get('wrong_solutions')
        wrong_solutions_str = "|".join(str(solution) for solution in wrong_solutions) if wrong_solutions else ""
        
        # Write penalties and wrong solutions to separate CSV
        penalties_csv_path = os.path.join(directory, "penalties.csv")
        with open(penalties_csv_path, "w") as f:
            f.write("experiment_id,task_id,penalty,wrong_solutions\n")
            f.write(f"{experiment_id},{task_id},{penalty},{wrong_solutions_str}\n")
        
        # Process goals in the checklist
        for i, goal in enumerate(checklist):
            if isinstance(goal, dict) and 'flag' in goal and 'weight' in goal:
                goal_desc = goal.get('id')
                achieved = goal['flag']
                weight = goal['weight']
                checklist_data.append([experiment_id, task_id, goal_desc, achieved, weight])
        
        # Save checklist data to CSV
        if checklist_data:
            checklist_csv_path = os.path.join(directory, "goal_achievement.csv")
            with open(checklist_csv_path, "w") as f:
                f.write("experiment_id,task_id,goal_description,achieved,weight\n")
                for row in checklist_data:
                    f.write(",".join(map(str, row)) + "\n")
            print(f"  - {checklist_csv_path}")
            print(f"  - {penalties_csv_path}")
    
    # Sort steps
    sorted_steps_data = OrderedDict(sorted(all_steps_data.items()))
    sorted_task_summary = OrderedDict(sorted(all_task_summary.items()))

    # Save eco metrics summary
    eco_output = OrderedDict()
    eco_output["cumulative"] = cumulative
    eco_output["steps"] = sorted_steps_data

    eco_output_path = os.path.join(directory, "eco_metrics_summary.json")
    with open(eco_output_path, "w") as f:
        json.dump(eco_output, f, indent=2)

    # Save task summary with step-wise cumulative rewards
    task_output_path = os.path.join(directory, "task_summary.json")
    with open(task_output_path, "w") as f:
        json.dump(sorted_task_summary, f, indent=2)

    # Save CSV data
    csv_output_path = os.path.join(directory, "task_stepwise_log.csv")
    with open(csv_output_path, "w") as f:
        f.write("step\tshop_id\taction\tused_axtree_object\turl\treward\tcumulative_reward\tthought\texperiment_id\ttask_id\n")
        for row in csv_data_all:
            f.write("\t".join(map(str, row)) + "\n")

    
    print(f"✅ Done. Results written to:\n  - {eco_output_path}\n  - {task_output_path}\n  - {csv_output_path}")
    # Also mention goal_achievement.csv if it was created
    if os.path.exists(os.path.join(directory, "goal_achievement.csv")):
        print(f"  - {os.path.join(directory, 'goal_achievement.csv')}")


if __name__ == "__main__":
    summarize_single_task(directory="/home/ralph/WebMall/AgentLab/study_results/genericagent-gpt-4o-2024-05-13-memory-on-webmall-a-c-d/GenericAgent-gpt-4o-2024-05-13-memory_on_webmall.Webmall_Best_Fit_Specific_Task1_1")
