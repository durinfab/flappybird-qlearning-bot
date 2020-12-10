class BongoBirdConfig(object):

    def __init__(self):
        self.playerVelY = -9  # player's velocity along Y, default same as playerFlapped
        self.playerMaxVelY = 10  # max vel along Y, max descend speed
        self.playerMinVelY = -8  # min vel along Y, max ascend speed
        self.playerAccY = 1  # players downward accleration
        self.playerFlapAcc = -2  # players speed on flapping
        self.playerFlapped = False  # True when player flaps
        self.SCREENWIDTH = 288
        self.SCREENHEIGHT = 512
        # amount by which base can maximum shift to left
        self.PIPEGAPSIZE = 100  # gap between upper and lower part of pipe
        self.BASEY = self.SCREENHEIGHT * 0.79

        # image width height indices for ease of use
        self.IM_WIDTH = 0
        self.IM_HEIGHT = 1
        # image, Width, Height
        self.PIPE = [52, 320]
        self.PLAYER = [34, 24]
        self.BASE = [336, 112]
        self.BACKGROUND = [288, 512]

class QLearningConfig(object):

    def __init__(self):
        self.gameCNT = 0  # Game count of current run, incremented after every death
        self.DUMPING_N = 25  # Number of iterations to dump Q values to JSON after
        self.discount = 1.0
        self.r = {0: 1, 1: -1000}  # Reward function
        self.lr = 0.7
        self.last_state = "420_240_0"
        self.last_action = 0
        self.moves = []