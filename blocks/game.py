from PyQt6.QtCore import pyqtSignal, QObject

from position import Position

from datetime import datetime
import string
import random

class Game(QObject):
    update_signal = pyqtSignal()
    end_signal = pyqtSignal(object)

    def __init__(self,player0,player1):
        super().__init__()
        self.position = Position()
        self.player=[None,None]
        self.slot=[self.move0,self.move1]
        self.active_player=0
        self.connectPlayer(0,player0)
        self.connectPlayer(1,player1)
        self.update_signal.emit()
        now=datetime.now()
        dt_string=now.strftime("%d_%m_%Y_%H_%M")
        self.game_name=dt_string
    def restart(self):
        self.position = Position()
        self.active_player=0
        self.winner=None
        self.draw=False
        self.update_signal.emit()
        self.ask_for_move()
        now=datetime.now()
        dt_string=now.strftime("%d_%m_%Y_%H_%M")
        self.game_name=dt_string
    def connectPlayer(self,index,player):
        previous = self.player[index]
        if(previous != None):
            previous.move_signal.disconnect(self.slot[index])
        player.move_signal.connect(self.slot[index])
        self.player[index]=player
        if(self.active_player==index):
            self.ask_for_move()
    def move0(self,i,k):
        self.move(0,i,k)
    def move1(self,i,k):
        self.move(1,i,k)
    def move(self,index,i,k):
        if(index != self.active_player):
            print("Disregarding move: Not your turn.")
        elif(self.position.move(i,k)):
            self.update_signal.emit()
            self.active_player = 1-self.active_player
            if self.position.over:
                self.end()
            else:
                self.ask_for_move()
    def ask_for_move(self):
        self.player[self.active_player].find_move(self.position)
    def end(self):
        if self.position.result == 0:
            self.end_signal.emit(None)
        else:
            self.end_signal.emit(1-self.active_player)
        for i in range(2):
            value = self.position.result #this is 0 if draw, 1 otherwise
            #1 represents a win for the player who is currently not active.
            #so if self.active_player != i, it is correct, otherwise flip
            if(i == self.active_player):
                value = -value
            if(hasattr(self.player[i],"save_experience")):
               suffix=''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
               self.player[i].save_experience(self.game_name + '_' + suffix, value)
