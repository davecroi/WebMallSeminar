# WebMall - A Multi-Shop Benchmark for Evaluating Web Agents

## Setting up WebMall

### Environment
- WebMall requires python 3.11/3.12
- WebMall requires a python environment without installed versions of BrowserGym and AgentLab, as we provide edited versions of BrowserGym and AgentLab which need local installation (steps below).

### Install local version of BrowserGym
- As we use a fork of BrowserGym and AgentLab as submodules, they must be initialized first with  ```git submodule update --init --recursive```
- Run ```make install``` in a terminal in the ```WebMall/BrowserGym``` folder to install BrowserGym and to install PlayWright to run experiments in a browser.

### Install local version of AgentLab
- Run ```pip install -e .``` in ```WebMall/AgentLab```

### Setup WebMall and AgentLab environment variables
- WebMall expects a file: WebMall/.env which contains env-variables setting the adresses to the shop websites. Make a copy of WebMall/.env.example and rename it to .env. Then set the variables SHOP1_URL, SHOP2_URL, SHOP3_URL, SHOP4_URL, FRONTEND_URL according to the shop adresses you want to use (if you use the local docker setup it uses localhost with ports 8081-8085, if the ports are available, the variables are correctly set).
- Set the environment variables:
  - AGENTLAB_EXP_ROOT=<root directory of experiment results>  # defaults to $HOME/agentlab_results this is where the experiment results will be stored.
  - OPENAI_API_KEY=<your openai api key> # if openai models are used set the OPEN AI API Key.
  - ANTHROPIC_API_KEY=<your anthropic api key> # if anthropic models are used set the ANTHROPIC API Key.

### Setup the WebMall Shops locally with Docker
1. The local docker setup requires docker-compose
2. Run ```bash docker_all/restore_all_and_deploy_local.sh``` to download the relevant files, start the containers and host the shops locally.
3. If you used the default ports, the setup is done, if not, you need to change the adresses inside the WooCommerce-Containers by running ```docker_all/fix_urls_deploy.sh``` for each of the 4 shops inside the respective docker-containers. 
Example: ```docker exec WebMall_wordpress_shop1 /bin/bash -c "/usr/local/bin/fix_urls_deploy.sh 'http://localhost:8081' 'http://localhost:7733'```
4. Verify the setup by visiting the Shop-Websites and the Submission page in your browser. 

## Running the WebMall benchmark
- A WebMall benchmark run can be started with the script ```WebMall/run_webmall_study.py```,
its results will be stored in the directory you set in AGENTLAB_EXP_ROOT. Set the task set you want to run by commenting in the relevant ```benchmark``` variable in the file.

## Running a single WebMall task
- A run for a single WebMall task can be started with the script ```WebMall/run_single_task.py```. Its results will be stored in the directory you set in AGENTLAB_EXP_ROOT.