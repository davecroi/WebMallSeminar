"""
Script to run a set of specific tasks
"""

import logging
import bgym
from dotenv import load_dotenv
from pathlib import Path
from webmall_overrides.env_args import EnvArgsWebMall
from webmall_overrides.exp_args import ExpArgsWebMall
# from agentlab.agents.generic_agent import (
#     AGENT_LLAMA3_70B,
#     AGENT_LLAMA31_70B,
#     RANDOM_SEARCH_AGENT,
#     AGENT_4o,
#     AGENT_4o_MINI,
# )

from agentlab.agents.visualwebmall_agent.agent import WA_AGENT_4O
#from agentlab.agents.webmall_generic_agent import AGENT_4o_VISION
from agentlab.agents.generic_agent import AGENT_4o_VISION

from agentlab.agents.most_basic_agent.most_basic_agent import MostBasicAgentArgs
from agentlab.llm.llm_configs import CHAT_MODEL_ARGS_DICT

from agentlab.experiments.launch_exp import run_experiments

from agentlab.agents import dynamic_prompting as dp
from agentlab.experiments import args
#from agentlab.llm.eco_logits_llm_configs import CHAT_MODEL_ARGS_DICT
from agentlab.llm.llm_configs import CHAT_MODEL_ARGS_DICT


#from agentlab.agents.webmall_generic_agent.generic_agent import GenericAgent, GenericPromptFlags, GenericAgentArgs
from agentlab.agents.generic_agent.generic_agent import GenericAgent, GenericPromptFlags, GenericAgentArgs

FLAGS_default = GenericPromptFlags(
    obs=dp.ObsFlags(
        use_html=False,
        use_ax_tree=True,
        use_focused_element=True,
        use_error_logs=True,
        use_history=True,
        use_past_error_logs=False,
        use_action_history=True,
        use_think_history=True,
        use_diff=False,
        html_type="pruned_html",
        use_screenshot=False,
        use_som=False,
        extract_visible_tag=True,
        extract_clickable_tag=True,
        extract_coords="False",
        filter_visible_elements_only=False,
    ),
    action=dp.ActionFlags(
        action_set=bgym.HighLevelActionSetArgs(
            subsets=["bid"],
            multiaction=False,
        ),
        long_description=False,
        individual_examples=False,
    ),
    use_plan=False,
    use_criticise=False,
    use_thinking=True,
    use_memory=False,
    use_concrete_example=True,
    use_abstract_example=True,
    use_hints=True,
    enable_chat=False,
    max_prompt_tokens=60_000,
    be_cautious=True,
    extra_instructions=None,
    )

FLAGS_T = FLAGS_default.copy()

FLAGS_T_V = FLAGS_default.copy()
FLAGS_T_V.obs.use_screenshot = True
FLAGS_T_V.obs.use_som = True

FLAGS_T_M = FLAGS_default.copy()
FLAGS_T_M.use_memory = True

FLAGS_T_V_M = FLAGS_default.copy()
FLAGS_T_V_M.obs.use_screenshot = True
FLAGS_T_V_M.obs.use_som = True
FLAGS_T_V_M.use_memory = True


AGENT_41_T = GenericAgentArgs(
    chat_model_args=CHAT_MODEL_ARGS_DICT["anthropic/claude-sonnet-4-20250514"],
    flags=FLAGS_T,
)


AGENT_41_T_V = GenericAgentArgs(
    chat_model_args=CHAT_MODEL_ARGS_DICT["anthropic/claude-sonnet-4-20250514"],
    flags=FLAGS_T_V,
)

AGENT_41_T_M = GenericAgentArgs(
    chat_model_args=CHAT_MODEL_ARGS_DICT["anthropic/claude-sonnet-4-20250514"],
    flags=FLAGS_T_M,
)

AGENT_41_T_V_M = GenericAgentArgs(
    chat_model_args=CHAT_MODEL_ARGS_DICT["anthropic/claude-sonnet-4-20250514"],
    flags=FLAGS_T_V_M,
)

# example for a single task
env_args = EnvArgsWebMall(
    task_name="webmall.Webmall_Best_Fit_Specific_Task6",
    task_seed=0,
    max_steps=30,
    headless=True,
    record_video=True
)



agent = AGENT_4o_VISION
agent.set_benchmark(bgym.DEFAULT_BENCHMARKS["webarena"](), demo_mode="off")

# example for 2 experiments testing chain of thoughts on a webmall task
#chat_model_args = CHAT_MODEL_ARGS_DICT["openai/gpt-4o-2024-05-13"]
#chat_model_args = CHAT_MODEL_ARGS_DICT["openai/gpt-4.1-2025-04-14"]
chat_model_args = CHAT_MODEL_ARGS_DICT["anthropic/claude-sonnet-4-20250514"]

exp_args = [
    # bgym.ExpArgs(
    #     agent_args=MostBasicAgentArgs(
    #         temperature=0.1,
    #         use_chain_of_thought=True,
    #         chat_model_args=chat_model_args,
    #     ),
    #     env_args=env_args,
    #     logging_level=logging.INFO,
    # ),
    ExpArgsWebMall(
        agent_args=agent,
        env_args=env_args,
        logging_level=logging.INFO,
    ),
]

current_file = Path(__file__).resolve()
PATH_TO_DOT_ENV_FILE = current_file.parent / ".env"
load_dotenv(PATH_TO_DOT_ENV_FILE)

if __name__ == "__main__":

    run_experiments(n_jobs=1, exp_args_list=exp_args, study_dir="task_results", parallel_backend="sequential")
