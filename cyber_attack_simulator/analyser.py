"""
This module contains functionallity for analysing and comparing agent
performance on Cyber Attack Simulator environments
"""
import numpy as np
import matplotlib.pyplot as plt
from textwrap import wrap


RESULTDIR = "results/"
FIGUREDIR = "figures/"


class Analyser(object):

    def __init__(self, env, agents, num_episodes, max_steps, num_runs):
        """
        Initialize for given network configuraiton and set of agents

        Arguments:
            CyberAttackSimulatorEnv env : environment object to test on
            list agents : list of Agent class instances
            int num_episodes : number of episodes to train agent for
            int max_steps : max number of steps per episode
            int num_runs : number of runs (i.e. set of episodes) to average
                results over
        """
        self.env = env
        self.agents = agents
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        self.num_runs = num_runs

        self.results = {}

    def run_analysis(self, verbose=True):
        """
        Run analysis for agents and environment

        Arguments:
            bool verbose : whether to print progress messages or not

        Returns:
            dict results : dict with agent type as key and values being
                npmatrix of rewards vs timesteps averaged over runs
        """
        print("Running analysis on: \n\t {0}\n".format(self.env))
        self.results = {}
        for agent in self.agents:
            print("Running analysis for agent {0}".format(str(agent)))
            run_steps = []
            run_rewards = []
            run_times = []
            for run in range(self.num_runs):
                print("Run {0} of {1}".format(run, self.num_runs))
                agent.reset()
                s, r, t = agent.train(self.env, self.num_episodes,
                                      self.max_steps, verbose)
                run_steps.append(s)
                run_rewards.append(r)
                run_times.append(t)
            self.results[agent.name()] = [np.average(run_steps, axis=0),
                                          np.average(run_rewards, axis=0),
                                          np.average(run_times, axis=0)]

    def plot_results(self):
        """
        Plot results of last analysis run
        """
        fig = plt.figure()
        title_text = "{0}, runs = {1}".format(self.env, self.num_runs)
        title = fig.suptitle("\n".join(wrap(title_text, 60)))

        ax1 = fig.add_subplot(131)
        for agent, result in self.results.items():
            ax1.plot(range(self.num_episodes), result[0], label=agent)

        ax1.set_xlabel("Episodes")
        ax1.set_ylabel("Average Timesteps")

        ax2 = fig.add_subplot(132)
        for agent, result in self.results.items():
            ax2.plot(range(self.num_episodes), result[1], label=agent)

        ax2.set_xlabel("Episodes")
        ax2.set_ylabel("Average Rewards")

        ax3 = fig.add_subplot(133)
        for agent, result in self.results.items():
            times = np.cumsum(result[2])
            ax3.plot(times, result[1], label=agent)

        ax3.set_xlabel("Average Time (sec)")
        ax3.set_ylabel("Average Rewards")

        handles, labels = ax3.get_legend_handles_labels()
        n_agents = len(self.agents)
        fig.legend(handles, labels, loc='lower center', ncol=n_agents // 2)

        fig.tight_layout()
        # set position for title and move plots down
        title.set_y(0.95)
        fig.subplots_adjust(top=0.85, left=0.1, right=0.9,
                            bottom=0.11 * (n_agents // 2))
        fig_name = self._output_file_name(FIGUREDIR, "png")
        fig.savefig(fig_name)
        plt.show()

    def output_results(self):
        """
        Output results to a file in csv format, with headers:

        agent,episode,timesteps,reward,time
        """
        file_name = self._output_file_name(RESULTDIR, "csv")
        fout = open(file_name, "w")
        fout.write("agent,episode,timesteps,reward,time\n")
        for agent, result in self.results.items():
            for e in range(self.num_episodes):
                output = ("{0},{1},{2},{3},{4}\n".format(agent, e,
                                                         result[0][e],
                                                         result[1][e],
                                                         result[2][e]))
                fout.write(output)
        fout.close()

    def _output_file_name(self, dir, filetype):
        name = "{0}{1}_{2}_{3}.{4}".format(dir,
                                           self.env.outfile_name(),
                                           len(self.agents),
                                           self.num_runs,
                                           filetype)
        return name