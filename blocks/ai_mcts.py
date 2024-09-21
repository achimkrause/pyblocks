from mcts import MCTSTree

import random as rnd
from PyQt6.QtCore import pyqtSignal, QObject

class AI_MCTS(QObject):
    additional_info_signal = pyqtSignal(object)

    def __init__(self,temperature=0.0):
        super().__init__()
        self.temperature=temperature
    def find_move(self,position):
        tree = MCTSTree(position)
        self.additional_info_signal.emit(tree)
        for n in range(500):
            tree.visit_child()
            self.additional_info_signal.emit(tree)
        policy=tree.compute_posterior_policy(self.temperature)
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


