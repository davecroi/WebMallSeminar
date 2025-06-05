import os
import gzip
import pickle
import re
import csv
import logging
import pandas as pd
import json
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, Tuple, Any, List


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the logging format and level.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=level
    )


def load_step(filepath: str) -> Any:
    """
    Load a single step object from a gzipped pickle file.

    Args:
        filepath: Path to the .pkl.gz file containing a StepInfo object.

    Returns:
        The unpickled StepInfo object.
    """
    with gzip.open(filepath, 'rb') as f:
        return pickle.load(f)

def has_search_and_product(url: str) -> bool:
    """
    Returns True if the URL has:
      - a query parameter 's' with any value
      - a query parameter 'post_type' equal to 'product'
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return 's' in qs and qs['s'][0] != '' and qs.get('post_type', []) == ['product']

def has_product_category(url: str) -> bool:
    """
    Returns True if 'product-category' appears as one of the path segments.
    """
    parsed = urlparse(url)
    # split the path into segments, e.g. "/a/b/" → ["a","b"]
    segments = [seg for seg in parsed.path.split('/') if seg]
    return 'product-category' in segments

def extract_category(url: str) -> str | None:
    """
    Extracts and returns the path segment right after 'product-category'.
    If 'product-category' is not present or has no following segment, returns None.
    """
    parsed = urlparse(url)
    # Break the path into non-empty segments
    segments = [seg for seg in parsed.path.split('/') if seg]

    idx = segments.index('product-category')
    # Return the next segment if it exists
    return '/'.join(segments[idx + 1:])

def is_product_detail(url: str) -> bool:
    """
    Returns True if the URL path matches exactly /product/<something>/ (one slug level),
    indicating a product detail page. Returns False otherwise.
    """
    parsed = urlparse(url)
    # strip trailing slash for easier matching
    path = parsed.path.rstrip('/')
    # pattern: start, /product/, then one or more non-slash chars, then end
    return bool(re.fullmatch(r'/product/[^/]+', path))

def extract_product_slug(url: str) -> str | None:
    """
    If the URL is of the form .../product/<slug>/, returns the <slug> (URL-decoded).
    Otherwise returns None.
    """
    parsed = urlparse(url)
    # split path into non-empty segments
    segments = [seg for seg in parsed.path.split('/') if seg]

    # find the "product" segment
    idx = segments.index('product')
    # return the next segment as the slug
    raw_slug = segments[idx + 1]
    return unquote(raw_slug)

def is_all_products_page(url: str) -> bool:
    """
    Returns True if the URL path is '/all-products' or '/all-products/'.
    """
    parsed = urlparse(url)
    # fullmatch will accept with or without trailing slash
    return bool(re.fullmatch(r'/all-products/?', parsed.path))


def classify_step(step: Any, last_url: str, double_action: bool) -> Tuple[str, str]:
    """
    Classify the type of page/action and extract a parameter for the step.

    Args:
        step: The StepInfo object for the current step.

    Returns:
        A tuple (action_type, parameter).

    NOTE:
        This function uses simple heuristics based on URL patterns and action strings.
        You may need to expand or refine these rules for your specific tasks.
    """
    # Safely extract action and URL, ensuring non-None
    action_raw = getattr(step, 'action', '') or ''
    action = action_raw.strip()
    url = getattr(step, 'obs', None).get('url') or ''

    # Default values
    action_type = 'unknown'
    parameter = ''
    shop_id = ''

    if 'localhost:8081' in url:
        shop_id = 'shop1'
    elif 'localhost:8082' in url:
        shop_id = 'shop2'
    elif 'localhost:8083' in url:
        shop_id = 'shop3'
    elif 'localhost:8084' in url:
        shop_id = 'shop4'
    elif 'localhost:8085' in url:
        shop_id = 'landing page'

    # Heuristic rules for actions
    if action.lower().startswith('scroll'):
        action_type = 'scroll'
    elif 'send_msg_to_user' in action.lower() and 'done' in action.lower():
        action_type = 'finished'
        parameter = action
    elif 'send_msg_to_user' in action.lower():
        action_type = 'answer'
        parameter = action
    elif url == 'http://localhost:8085/' and last_url != 'http://localhost:8085/' and not double_action:
        action_type = 'Visit landing page'
        if action.lower().startswith("fill("):
            double_action = True
    elif url == 'http://localhost:8081/' and last_url != 'http://localhost:8081/' and not double_action:
        action_type = 'Visit shop1 landing page'
        if action.lower().startswith("fill("):
            double_action = True
    elif url == 'http://localhost:8082/' and last_url != 'http://localhost:8082/' and not double_action:
        action_type = 'Visit shop2 landing page'
        if action.lower().startswith("fill("):
            double_action = True
    elif url == 'http://localhost:8083/' and last_url != 'http://localhost:8083/' and not double_action:
        action_type = 'Visit shop3 landing page'
        if action.lower().startswith("fill("):
            double_action = True
    elif url == 'http://localhost:8084/' and last_url != 'http://localhost:8084/' and not double_action:
        action_type = 'Visit shop4 landing page'
        if action.lower().startswith("fill("):
            double_action = True
    elif action.lower().startswith('click') and getattr(step, 'obs', None).get('last_action').lower().startswith("fill("):
        action_type = 'perform search'
    elif has_product_category(url) and not double_action:
        action_type = 'view category page'
        parameter = extract_category(url)
        if action.lower().startswith("fill("):
            double_action = True
    elif action.lower().startswith("fill("):
        action_type = 'fill search form'
        # extract search text from action
        sep = "', '"
        start = action.find(sep) + len(sep)
        end = action.rfind("')")
        parameter = action[start:end]
    elif has_search_and_product(url):
        action_type = 'view search result page'
    elif is_product_detail(url):
        action_type = 'view product detail page'
        parameter = extract_product_slug(url)
    elif is_all_products_page(url):
        action_type = 'view all products page'
    elif getattr(step, 'terminated', False):
        action_type = 'finished'
        parameter = action
    elif getattr(step, 'truncated', False):
        action_type = 'finished due to step limit'
    elif action.lower().startswith('click'):
        action_type = 'click'
    # leave defaults otherwise
    last_url = url
    last_action_type = action

    return action_type, parameter, shop_id, last_url, double_action


def parse_step(step: Any, run_id: str, task_id: str, step_index: int, last_url: str, double_action: bool, cur_reward: float, track_reward: bool = True) -> Dict[str, Any]:
    """
    Extract relevant fields from a StepInfo object into a flat dictionary.

    Args:
        step: The StepInfo object to parse.
        run_id: Identifier of the study run.
        task_id: Identifier of the task within the study.
        shop_id: Optional shop identifier if applicable.

    Returns:
        A dict mapping column names to values.
    """

    

    action_type, parameter, shop_id, last_url, double_action = classify_step(step, last_url, double_action)

    # skip step if last action was an answer
    if 'last_action_type' in locals() and last_action_type == 'answer':
         return {}, last_url, double_action, cur_reward

    last_action_type = action_type

    # Skip step if action type is unknown
    if action_type == 'unknown' or action_type == 'scroll' or action_type == 'click':
        return {}, last_url, double_action, cur_reward

    url = getattr(step, 'obs', None).get('url')

    if track_reward:
        reward = getattr(step, 'reward')
        cur_reward += reward
    else:
        reward = 0

    return {
        'step': step_index,
        'browsergym_step': getattr(step, 'step'),
        'shopID': shop_id,
        'type_of_page_action': action_type,
        'parameter': parameter,
        'reward_current_step': reward,
        'accumulated_reward': cur_reward,
        'URL': url,
        'runID': run_id,
        'taskID': task_id,
    }, last_url, double_action, cur_reward


def process_task_folder(task_path: str, run_id: str, task_id: str) -> List[Dict[str, Any]]:
    """
    Iterate over all step files in a task folder and parse each into a row dict.
    """
    rows: List[Dict[str, Any]] = []
    files = sorted(
        [f for f in os.listdir(task_path) if f.startswith('step_') and f.endswith('.pkl.gz')],
        key=lambda x: int(x.split('_')[1].split('.')[0])
    )

    # track step index
    cur_index = 0
    # track last visited URL
    last_url = ''
    # track reward accumulation
    cur_reward = 0

    for fname in files:
        fpath = os.path.join(task_path, fname)

        double_action = False
        step = load_step(fpath)
        row, last_url, double_action, cur_reward = parse_step(step, run_id, task_id, step_index=cur_index, last_url=last_url, double_action=double_action, cur_reward=cur_reward)

        # check if returned dict is empty and continue to next step
        if not row:
            continue

        rows.append(row)
        cur_index += 1

        if row['type_of_page_action'] == 'finished':
            break

        if double_action:
            row, last_url, double_action, cur_reward = parse_step(step, run_id, task_id, step_index=cur_index, last_url=last_url, double_action=double_action, cur_reward=cur_reward, track_reward=False)
            
            if not row:
                continue

            rows.append(row)
            cur_index += 1

    return rows


def consolidate_study(study_path: str, output_root: str = '.') -> None:
    """
    Process all tasks in a study folder, writing a CSV for each task.
    """
    study_name = os.path.basename(study_path.rstrip(os.sep))

    for task_dir in os.listdir(study_path):
        task_path = os.path.join(study_path, task_dir)
        if not os.path.isdir(task_path):
            continue

        logging.info(f"Processing study '{study_name}', task '{task_dir}'...")
        rows = process_task_folder(task_path, run_id=study_name, task_id=task_dir.split('.')[-1])
        if not rows:
            logging.info(f"No steps found for {task_dir}, skipping CSV generation.")
            continue

        output_file = os.path.join(output_root, f"{study_name}_{task_dir}_steps.csv")
        output_file_goal = os.path.join(output_root, f"{study_name}_{task_dir}_goal.txt")
        os.makedirs(output_root, exist_ok=True)

        goal_object = pd.read_pickle(task_path + "/goal_object.pkl.gz")

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        with open(output_file_goal, 'w', encoding='utf-8') as f:
            json.dump(goal_object, f, indent=2, ensure_ascii=False)


        logging.info(f"Wrote {len(rows)} steps to {output_file}")


if __name__ == '__main__':
    setup_logging()
    base = 'AgentLab/study_results'
    if not os.path.isdir(base):
        logging.error(f"Study results directory not found: {base}")
    else:
        for study in os.listdir(base):
            study_path = os.path.join(base, study)
            if os.path.isdir(study_path):
                consolidate_study(study_path, output_root='./outputs')
