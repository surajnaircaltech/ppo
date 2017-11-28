import network
import build_graph
import lightsaber.tensorflow.util as util
import numpy as np
import tensorflow as tf


class Agent(object):
    def __init__(self, network, obs_dim, num_actions, gamma=0.9, reuse=None):
        self.num_actions = num_actions
        self.gamma = gamma
        self.t = 0
        self.obss = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.next_values = []

        act, train, update_old, backup_current = build_graph.build_train(
            network=network,
            obs_dim=obs_dim,
            num_actions=num_actions,
            gamma=gamma,
            reuse=reuse
        )
        self._act = act
        self._train = train
        self._update_old = update_old
        self._backup_current = backup_current

    def act(self, obs):
        return self._act([obs])[0][0]

    def act_and_train(self, last_obs, last_action, last_value, reward, obs):
        action, value = self._act([obs])
        action = action[0]
        value = value[0]
        action = np.clip(action, -1, 1)

        if last_obs is not None:
            self._add_trajectory(
                last_obs,
                last_action,
                reward,
                last_value,
                value
            )

        self.t += 1
        return action, value

    def train(self, obs, actions, returns, deltas):
        self._backup_current()
        print(self._train(obs, actions, returns, deltas))
        self._update_old()

    def stop_episode(self, last_obs, last_action, last_value, reward):
        self._add_trajectory(
            last_obs,
            last_action,
            reward,
            last_value,
            0
        )

    def _reset_trajectories(self):
        self.obss = []
        self.rewards = []
        self.actions = []
        self.values = []
        self.next_values = []

    def _add_trajectory(self, obs, action, reward, value, next_value):
        self.obss.append(obs)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.next_values.append(next_value)

    def get_training_data(self):
        obss = list(self.obss)
        actions = list(self.actions)
        returns = []
        deltas = []
        for i in reversed(range(len(self.obss))):
            reward = self.rewards[i]
            value = self.values[i]
            next_value = self.next_values[i]
            delta = reward + self.gamma * next_value - value
            returns.append(delta + value)
            deltas.append(delta)
        returns = np.array(returns, dtype=np.float32)
        deltas = np.array(deltas, dtype=np.float32)
        # standardize advantages
        deltas = (deltas - deltas.mean()) / deltas.std()
        self._reset_trajectories()
        return obss, actions, list(returns), list(deltas)

    def sync_old(self):
        self._update_old()
