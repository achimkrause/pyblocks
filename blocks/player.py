
from PyQt6.QtCore import pyqtSignal, QObject

#abstract
class PlayerTemplate:
    def __init__(self):
        pass
    def new(self):
        return Player()

#just to check whether needs to be connected to UI
class HumanPlayerTemplate(PlayerTemplate):
    def __init__(self):
        pass
    def new(self):
        return Player()

class Player(QObject):
    move_signal = pyqtSignal(int,int) #to be listened to by game
    additional_info_signal = pyqtSignal(object) #to be listened to by board_game_area
    def __init__(self):
        self.turn = False
        super().__init__()
    def find_move(self,position):
        self.turn = True
    def make_move(self,i,k):
        if not self.turn:
            return
        self.turn = False
        self.move_signal.emit(i,k)
    def game_end(self,game_name,value):
        pass
