# WebMall - A Multi-Shop Benchmark for Evaluating Web Agents

🌐 [WebMall Website](https://wbsg-uni-mannheim.github.io/WebMall/)  
📄 [Paper](https://arxiv.org/abs/2508.13024)

## Abstract

This repository contains the code and data of the WebMall benchmark for evaluating the capability of Web agents to find and compare product offers from multiple e-shops. The benchmark features two sets of tasks: A set containing basic tasks like searching and comparing offers, adding offers to the shopping cart, and finally checking out the selected offers. The benchmark also features an advanced task set containing searches with vague requirements as well as searches for compatible products or cheaper substitute products.

For more detailed information about the benchmark design, task specifications, and initial results, please refer to our [website](https://wbsg-uni-mannheim.github.io/WebMall/).

## Setting up WebMall

### Environment

-   WebMall requires python 3.11/3.12
-   WebMall requires a python environment without installed versions of BrowserGym and AgentLab, as we provide edited versions of BrowserGym and AgentLab which need local installation (steps below).

### Install local version of BrowserGym

-   As we use a fork of BrowserGym and AgentLab as submodules, they must be initialized first with `git submodule update --init --recursive`
-   Run `make install` in a terminal in the `WebMall/BrowserGym` folder to install BrowserGym and to install PlayWright to run experiments in a browser.

### Install local version of AgentLab

-   Run `pip install -e .` in `WebMall/AgentLab`

### Setup WebMall and AgentLab environment variables

-   WebMall expects a file: WebMall/.env which contains env-variables setting the adresses to the shop websites. Make a copy of WebMall/.env.example and rename it to .env. Then set the variables SHOP1_URL, SHOP2_URL, SHOP3_URL, SHOP4_URL, FRONTEND_URL according to the shop adresses you want to use (if you use the local docker setup it uses localhost with ports 8081-8085, if the ports are available, the variables are correctly set).
-   Set the environment variables:
    -   AGENTLAB_EXP_ROOT=<root directory of experiment results> # defaults to $HOME/agentlab_results this is where the experiment results will be stored.
    -   OPENAI_API_KEY=<your openai api key> # if openai models are used set the OPEN AI API Key.
    -   ANTHROPIC_API_KEY=<your anthropic api key> # if anthropic models are used set the ANTHROPIC API Key.

### Setup the WebMall Shops locally with Docker

See the [Docker setup README](docker_all/README.md) for detailed instructions on setting up the local Docker environment.

## Running the WebMall benchmark

-   A WebMall benchmark run can be started with the script `WebMall/run_webmall_study.py`,
    its results will be stored in the directory you set in AGENTLAB_EXP_ROOT. Set the task set you want to run by commenting in the relevant `benchmark` variable in the file.

## Running a single WebMall task

-   A run for a single WebMall task can be started with the script `WebMall/run_single_task.py`. Its results will be stored in the directory you set in AGENTLAB_EXP_ROOT.
