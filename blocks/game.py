from PyQt6.QtCore import pyqtSignal, QObject

from position import Position

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
        self.winner=None
        self.draw=False
        self.update_signal.emit()
    def restart(self):
        self.position = Position()
        self.active_player=0
        self.winner=None
        self.draw=False
        self.update_signal.emit()
        print("requested move {}".format(0))
        self.ask_for_move()
    def connectPlayer(self,index,player):
        print("switched player {}".format(index))
        previous = self.player[index]
        if(previous != None):
            previous.move_signal.disconnect(self.slot[index])
        player.move_signal.connect(self.slot[index])
        self.player[index]=player
        if(self.active_player==index):
            print("requested move {}".format(index))
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
                if self.position.result == 0:
                    self.end_signal.emit(None)
                else:
                    self.end_signal.emit(1-self.active_player)
            else:
                self.ask_for_move()
    def ask_for_move(self):
        self.player[self.active_player].find_move(self.position)
        

