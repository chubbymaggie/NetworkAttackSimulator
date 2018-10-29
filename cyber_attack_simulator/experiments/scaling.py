"""
This module contains functions for performing an analysis of the performance of different
algorithms versus the problem size (number of machines and exploits)
"""
from cyber_attack_simulator.envs.environment import CyberAttackSimulatorEnv as Cyber
from cyber_attack_simulator.agents.q_learning import QLearningAgent
from cyber_attack_simulator.agents.dqn import DQNAgent
from collections import OrderedDict
import time
import sys
import numpy as np


# Experiment agents
agents = OrderedDict()
# agents["td_egreedy"] = {
#     "type": "egreedy", "alpha": 0.05, "gamma": 0.9, "epsilon_decay_lambda": 0.01
#     }
# agents["td_ucb"] = {
#     "type": "UCB", "alpha": 0.05, "gamma": 0.9, "c": 1.0
#     }
agents["dqn"] = {
    "hidden_units": 256, "gamma": 0.5, "epsilon_decay_lambda": 0.01
    }

# Experiment parameters
RUNS = 5
MACHINE_MIN = 27
MACHINE_MAX = 29
MACHINE_INTERVAL = 2
MAX_EPISODES = 10000
EPISODE_INTERVALS = 100
MAX_STEPS = 200
EVAL_RUNS = 100
OPTIMALITY_PROPORTION = 7.0
OPTIMAL_SOLVE_PROPORTION = 0.9  # proportion of trials to solve to be considered solved
TIMEOUT = 200
VERBOSE = False

# Environment constants
SERVICES = 5
RVE = 3         # restrictiveness
UNIFORM = False
EXPLOIT_PROB = 0.7
R_SENS = R_USR = 10
COST_EXP = COST_SCAN = 1


def run_scaling_analysis(agent_type, result_file):

    print("\nRunning scaling analysis for agent: \n\t {0}".format(str(agent_type)))
    for m in range(MACHINE_MIN, MACHINE_MAX + 1, MACHINE_INTERVAL):
        solve_times = []
        one_run_solved = False
        print("\n>> Machines={0}".format(m))
        for t in range(RUNS):
            print("\tRun {0} of {1}".format(t+1, RUNS))
            env = Cyber.from_params(m, SERVICES,
                                    r_sensitive=R_SENS,  r_user=R_USR,
                                    exploit_cost=COST_EXP, scan_cost=COST_SCAN,
                                    restrictiveness=RVE, exploit_probs=EXPLOIT_PROB, seed=t)
            agent = get_agent(agent_type, env)
            solved, solve_time, mean_reward = run_till_solved(agent, env)
            solve_times.append(solve_time)
            write_results(result_file, agent_type, m, t, solved, solve_time, mean_reward)
            print("\t\tsolved={} -- solve_time={:.2f} -- mean_reward={}"
                  .format(solved, solve_time, mean_reward))
            if solved:
                one_run_solved = True
        print(">> Average solve time = {}".format(np.mean(solve_times)))
        if not one_run_solved:
            print(">> No environments solved so not testing larger sizes")
            break


def write_results(result_file, agent, M, run, solved, solve_time, mean_reward):
    """ Write results to file """
    # agent,machines,run,solved,solve_time, total_reward
    result_file.write("{0},{1},{2},{3},{4:.2f},{5}\n"
                      .format(agent, M, run, solved, solve_time, mean_reward))


def run_till_solved(agent, env):

    solved = False
    episodes = 0
    start_time = time.time()
    mean_solution_reward = 0
    while not solved and episodes < MAX_EPISODES:
        agent.train(env, EPISODE_INTERVALS, MAX_STEPS, timeout=TIMEOUT, verbose=VERBOSE)
        episodes += EPISODE_INTERVALS
        solved, mean_solution_reward = environment_solved(agent, env)
        if time.time() - start_time > TIMEOUT:
            break
    run_time = time.time() - start_time
    return solved, run_time, mean_solution_reward


def environment_solved(agent, env):
    min_actions = env.get_minimum_actions()
    optimal_threshold = int(round(min_actions * OPTIMALITY_PROPORTION))
    solved_runs = 0
    total_reward = 0
    for r in range(EVAL_RUNS):
        episode = agent.generate_episode(env, optimal_threshold)
        if len(episode) < optimal_threshold:
            solved_runs += 1
            total_reward += get_episode_reward(episode)

    if solved_runs == 0:
        mean_reward = 0
    else:
        mean_reward = total_reward / solved_runs

    return solved_runs / EVAL_RUNS > OPTIMAL_SOLVE_PROPORTION, mean_reward


def get_episode_reward(episode):
    return episode[-1][2]


def get_agent(agent_name, env):
    """ Returns a new agent instance """
    agent_params = agents[agent_name]
    if agent_name == "dqn":
        state_size = env.get_state_size()
        num_actions = env.get_num_actions()
        return DQNAgent(state_size, num_actions, **agent_params)
    return QLearningAgent(**agent_params)


def main():

    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage: python analysis_scaling.py outfile [1/0]")
        print("Where the [1/0] is for whether to append to file or not")
        return 1

    print("Welcome to your friendly scaling experiment runner")
    if len(sys.argv) == 3 and sys.argv[2] == "1":
        print("Appending to", sys.argv[1])
        result_file = open(sys.argv[1], 'a+')
    else:
        print("Writing to new file", sys.argv[1])
        result_file = open(sys.argv[1], 'w')
        # write header line
        result_file.write("agent,M,run,solved,solve_time,mean_reward\n")

    for agent_type in agents.keys():
        run_scaling_analysis(agent_type, result_file)

    result_file.close()


if __name__ == "__main__":
    main()