import json
from config import QLearningConfig


class Bot(object):
    """
    The Bot class that applies the Qlearning logic to Flappy bird game
    After every iteration (iteration = 1 game that ends with the bird dying) updates Q values
    After every DUMPING_N iterations, dumps the Q values to the local JSON file
    """
    config = QLearningConfig()

    gameCNT     = config.gameCNT  # Game count of current run, incremented after every death
    DUMPING_N   = config.DUMPING_N  # Number of iterations to dump Q values to JSON after
    discount    = config.discount
    r           = config.r  # Reward function
    gamma       = config.gamma

    last_state = config.last_state
    last_action = config.last_action
    moves = config.moves

    def __init__(self):
        self.load_qvalues()

    def load_qvalues(self):
        """
        Load q values from a JSON file
        """
        self.qvalues = {}
        self.frequency = {}
        try:
            fil = open("data/qvalues.json", "r")
            fil2 = open("data/frequency.json", "r")
        except IOError:
            return
        self.qvalues = json.load(fil)
        self.frequency = json.load(fil2)
        fil.close()
        fil2.close()

    def act(self, xdif, ydif, vel):
        """
        Chooses the best action with respect to the current state - Chooses 0 (don't flap) to tie-break
        """
        state = self.map_state(xdif, ydif, vel)

        self.moves.append(
            (self.last_state, self.last_action, state)
        )  # Add the experience to the history

        self.last_state = state  # Update the last_state with the current state

        if self.qvalues[state][0] >= self.qvalues[state][1]:
            self.last_action = 0
            return 0
        else:
            self.last_action = 1
            return 1

    def update_scores(self, dump_qvalues=True):
        """
        Update qvalues via iterating over experiences
        """
        history = list(reversed(self.moves))

        # Flag if the bird died in the top pipe
        high_death_flag = True if int(history[0][2].split("_")[1]) > 120 else False

        # Q-learning score updates
        t = 1
        k = 1 # loop counter
        for exp in history:
            state = exp[0]
            act = exp[1]
            res_state = exp[2]

            # Select reward
            if t == 1 or t == 2:
                cur_reward = self.r[1]
            elif high_death_flag and act:
                cur_reward = self.r[1]
                high_death_flag = False
            else:
                cur_reward = self.r[0]

            # Update

            # passive learning TD agent
            #   Uπ(s) <- Uπ(s) + α( R(s) + γ Uπ(s′) − Uπ(s) )
            # note: alpha should be fixed value
            #       gamma should be 1
            # self.qvalues[state][act] = self.qvalues[state][act] + self.alpha(cur_reward + self.gamma * max(self.qvalues[res_state]) - self.qvalues[state][act] )

            #   U[s] <- U[s] + α(Ns[s])(r + γ U[s'] − U[s])
            #   here alpha should decrease with a higher frequency of the s/a pair
            self.frequency[state][act] += 1
            self.qvalues[state][act] = self.qvalues[state][act] + self.alpha_2(self.frequency[state][act]) * (cur_reward + self.gamma * max(self.qvalues[res_state]) - self.qvalues[state][act] )

            # discount factor in [0, 1]
            # If 𝛾 = 0, the agent cares for his first reward only.
            # If 𝛾 = 1, the agent cares for all future rewards.
            self.gamma = 1

            # increment time
            t += 1
            k += 1

        self.gameCNT += 1  # increase game count
        if dump_qvalues:
            self.dump_qvalues()  # Dump q values (if game count % DUMPING_N == 0)
        self.moves = []  # clear history after updating strategies

    def map_state(self, xdif, ydif, vel):
        """
        Map the (xdif, ydif, vel) to the respective state, with regards to the grids
        The state is a string, "xdif_ydif_vel"

        X -> [-40,-30...120] U [140, 210 ... 420]
        Y -> [-300, -290 ... 160] U [180, 240 ... 420]
        """
        if xdif < 140:
            xdif = int(xdif) - (int(xdif) % 10)
        else:
            xdif = int(xdif) - (int(xdif) % 70)

        if ydif < 180:
            ydif = int(ydif) - (int(ydif) % 10)
        else:
            ydif = int(ydif) - (int(ydif) % 60)

        return str(int(xdif)) + "_" + str(int(ydif)) + "_" + str(vel)

    # learning rate (ensures convergence)
    def alpha(self, n):
        #print(n)
        #i = 99 + n
        #i = 100/i
        i = 0.7 * n
        return i

    # learning rate (ensures convergence)
    # for when we use frequencies
    def alpha_2(self, n):
        #print(n)
        #i = 99 + n
        #i = 100/i
        # i = 0.7 * n
        if n == 0:
            i = 1
        else:
            i = 0.7

        return i

    def dump_qvalues(self, force=False):
        """
        Dump the qvalues to the JSON file
        """
        if self.gameCNT % self.DUMPING_N == 0 or force:
            print("start q dump")
            fil = open("data/qvalues.json", "w")
            json.dump(self.qvalues, fil)
            fil.close()
            print("end q dump")
            fil2 = open("data/frequency.json", "w")
            json.dump(self.frequency, fil2)
            fil2.close()
            print("Q-values updated on local file.")
