from itertools import cycle
import random
import sys
import os
import argparse
import pickle
import json
from itertools import chain

import pygame
from pygame.locals import *

sys.path.append(os.getcwd())

from config import BongoBirdConfig
from bot import Bot

config = BongoBirdConfig()

SCREENWIDTH = config.SCREENWIDTH
SCREENHEIGHT = config.SCREENHEIGHT
# amount by which base can maximum shift to left
PIPEGAPSIZE = config.PIPEGAPSIZE  # gap between upper and lower part of pipe
BASEY = config.BASEY

# image width height indices for ease of use
IM_WIDTH = config.IM_WIDTH
IM_HEIGHT = config.IM_HEIGHT
# image, Width, Height
PIPE = config.PIPE
PLAYER = config.PLAYER
BASE = config.BASE
BACKGROUND = config.BACKGROUND

def main():
    global HITMASKS, ITERATIONS, VERBOSE, bot

    # argumente
    parser = argparse.ArgumentParser("learn.py")
    parser.add_argument("--iter", type=int, default=1000, help="number of iterations to run")
    parser.add_argument("--reset", action="store_true", help="reset qvales on startup")
    parser.add_argument(
        "--verbose", action="store_true", help="output [iteration | score] to stdout"
    )
    args = parser.parse_args()
    ITERATIONS = args.iter
    VERBOSE = args.verbose

    #reset collected qvalues
    if args.reset:
        print("Resetting values...")
        qval = {}
        frequency = {}
        # X -> [-40,-30...120] U [140, 210 ... 490]
        # Y -> [-300, -290 ... 160] U [180, 240 ... 420]
        for x in chain(list(range(-40, 140, 10)), list(range(140, 421, 70))):
            for y in chain(list(range(-300, 180, 10)), list(range(180, 421, 60))):
                for v in range(-10, 11):
                    qval[str(x) + "_" + str(y) + "_" + str(v)] = [0, 0]
                    frequency[str(x) + "_" + str(y) + "_" + str(v)] = [0, 0]


        fd = open("data/qvalues.json", "w")
        fd2 = open("data/frequency.json", "w")

        json.dump(qval, fd)
        json.dump(frequency, fd2)

        fd.close()
        fd2.close()
        print("Reset complete!")

    # init bot
    bot = Bot()

    # load dumped HITMASKS
    with open("data/hitmasks_data.pkl", "rb") as input:
        HITMASKS = pickle.load(input)

    while True:
        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


def showWelcomeAnimation():
    """Shows welcome screen animation of flappy bird"""
    # index of player to blit on screen
    playerIndexGen = cycle([0, 1, 2, 1])

    playery = int((SCREENHEIGHT - PLAYER[IM_HEIGHT]) / 2)

    basex = 0

    # player shm for up-down motion on welcome screen
    playerShmVals = {"val": 0, "dir": 1}

    return {
        "playery": playery + playerShmVals["val"],
        "basex": basex,
        "playerIndexGen": playerIndexGen,
    }


def mainGame(movementInfo):

    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo["playerIndexGen"]

    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo["playery"]

    basex = movementInfo["basex"]
    baseShift = BASE[IM_WIDTH] - BACKGROUND[IM_WIDTH]

    # get 2 new pipes to add to upperPipes lowerPipes list
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # list of initial upper pipes
    upperPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[0]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[0]["y"]},
    ]

    # list of initial lowerpipe
    lowerPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[1]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[1]["y"]},
    ]

    pipeVelX = -4

    # player velocity, max velocity, downward accleration, accleration on flap
    playerVelY      = config.playerVelY  # player's velocity along Y, default same as playerFlapped
    playerMaxVelY   = config.playerMaxVelY  # max vel along Y, max descend speed
    playerMinVelY   = config.playerMinVelY  # min vel along Y, max ascend speed
    playerAccY      = config.playerAccY  # players downward accleration
    playerFlapAcc   = config.playerFlapAcc  # players speed on flapping
    playerFlapped   = config.playerFlapped  # True when player flaps

    # play until we die
    while True:
        # is lowerpipe[0] still in front of us?
        if -playerx + lowerPipes[0]["x"] > -30:
            myPipe = lowerPipes[0]
        else:
            myPipe = lowerPipes[1]

        # state:
        # value to determine the x relation between play and pipe
        # ,value to determine the y relation between play and pipe
        # ,player velocity along y
        if bot.act(-playerx + myPipe["x"], -playery + myPipe["y"], playerVelY):

            playerVelY = playerFlapAcc
            playerFlapped = True

        # check for crash here
        crashTest = checkCrash(
            {"x": playerx, "y": playery, "index": playerIndex}, upperPipes, lowerPipes
        )
        if crashTest[0]:
            # Update the q scores
            bot.update_scores(dump_qvalues=False)

            return {
                "y": playery,
                "groundCrash": crashTest[1],
                "basex": basex,
                "upperPipes": upperPipes,
                "lowerPipes": lowerPipes,
                "score": score,
                "playerVelY": playerVelY,
            }

        # check for score
        playerMidPos = playerx + PLAYER[IM_WIDTH] / 2
        for pipe in upperPipes:
            pipeMidPos = pipe["x"] + PIPE[IM_WIDTH] / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1

        # playerIndex basex change
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        # player's movement
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False
        playerHeight = PLAYER[IM_HEIGHT]
        playery += min(playerVelY, BASEY - playery - playerHeight)

        # move pipes to left
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe["x"] += pipeVelX
            lPipe["x"] += pipeVelX

        # add new pipe when first pipe is about to touch left of screen
        if 0 < upperPipes[0]["x"] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if upperPipes[0]["x"] < -PIPE[IM_WIDTH]:
            upperPipes.pop(0)
            lowerPipes.pop(0)


def showGameOverScreen(crashInfo):
    if VERBOSE:
        score = crashInfo["score"]
        print(str(bot.gameCNT - 1) + " | " + str(score))

    if bot.gameCNT == (ITERATIONS):
        bot.dump_qvalues(force=True)
        sys.exit()


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm["val"]) == 8:
        playerShm["dir"] *= -1

    if playerShm["dir"] == 1:
        playerShm["val"] += 1
    else:
        playerShm["val"] -= 1


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = PIPE[IM_HEIGHT]
    pipeX = SCREENWIDTH + 10

    return [
        {"x": pipeX, "y": gapY - pipeHeight},  # upper pipe
        {"x": pipeX, "y": gapY + PIPEGAPSIZE},  # lower pipe
    ]


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""
    pi = player["index"]
    player["w"] = PLAYER[IM_WIDTH]
    player["h"] = PLAYER[IM_HEIGHT]

    # if player crashes into ground
    if (player["y"] + player["h"] >= BASEY - 1) or (player["y"] + player["h"] <= 0):
        return [True, True]
    else:

        playerRect = pygame.Rect(player["x"], player["y"], player["w"], player["h"])
        pipeW = PIPE[IM_WIDTH]
        pipeH = PIPE[IM_HEIGHT]

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe["x"], uPipe["y"], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe["x"], lPipe["y"], pipeW, pipeH)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS["player"][pi]
            uHitmask = HITMASKS["pipe"][0]
            lHitmask = HITMASKS["pipe"][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


if __name__ == "__main__":
    main()
