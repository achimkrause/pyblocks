from mcts import MCTSTree,VPFunction
from learning import NN_VPFunction
from ai import AITemplate, AI

import numpy as np
import random as rnd
import string
from PyQt6.QtCore import pyqtSignal, QObject

from pathlib import Path

class AIMCTSTemplate(AITemplate):
    def __init__(self, path=None, training=False,initialize=False):
        super().__init__()
        self.path = path
        self.training = training
        self.initialize = initialize
    def new(self):
        return AIMCTS(self.path,self.training,self.initialize)


class AIMCTS(AI):
    additional_info_signal = pyqtSignal(object)

    def __init__(self,path=None,training=False,initialize=False):
        super().__init__()
        if(path==None):
            self.path=None
            self.vp_function = VPFunction()
        else:
            self.path = Path(path)
            if(initialize):
                self.generate_files()
            self.vp_function = NN_VPFunction(self.path / 'model.weights',initialize)
        self.training=training
        if(training):
            self.temperature=1.0
        else:
            self.temperature=0.2
        self.exp_list_player0 = []
        self.exp_list_player1 = []
        self.exp_list_target_policy = []
    def generate_files(self):
        self.path.mkdir()
        (self.path/'games').mkdir()
    def find_move(self,position):
        tree = MCTSTree(self.vp_function, position)
        self.additional_info_signal.emit(tree)
        for n in range(500):
            tree.visit_child()
            self.additional_info_signal.emit(tree)
        policy=tree.compute_posterior_policy(self.temperature)
        if(self.training):
            experience=tree.compute_experience() #we need to collect these, together with the true outcome of the game, and store them on file
            self.append_experience(experience)
        t = rnd.random()
        for i in range(11):
            for k in range(17):
                t -= policy[i][k]
                if t<0:
                    return (i,k)
        #we only land here if t was almost exactly 1, in that case take first possible move.
        for i in range(11):
            for k in range(17):
                if position.valid_moves[i][k]:
                    return (i,k)
    def append_experience(self,experience):
        self.exp_list_player0.append(experience.player0_pieces)
        self.exp_list_player1.append(experience.player1_pieces)
        self.exp_list_target_policy.append(experience.posterior_policy)
    def train(self, game_name, value):
        if not self.training:
            return
        if self.path == None:
            print("Training without path doesn't work")
            return
        n = len(self.exp_list_player0)
        player0 = np.array(self.exp_list_player0)
        player1 = np.array(self.exp_list_player1)
        target_policy = np.array(self.exp_list_target_policy)
        target_value = np.full((n,1),value)
        suffix=''.join(rnd.choices(string.ascii_uppercase + string.digits, k=6))
        savepath = self.path / 'games' / (game_name + '_' + suffix)
        print("saving {}".format(savepath))
        np.savez(savepath,player0=player0, player1=player1, target_policy=target_policy, target_value=target_value)





