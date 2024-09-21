import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor
import numpy as np

from position import Position
from game import Game
from ai_random import AIRandom
from ai_mcts import AI_MCTS
from ai import AIPlayer

import argparse

dotColor = QColor(200,200,200)
playerColor = [QColor(75,75,75),QColor(227,225,161)]
textColor = QColor(0,0,255)

radius=5
click_radius=10

class Player(QObject):
    move_signal = pyqtSignal(int,int)
    move_requested_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
    def find_move(self,position):
        self.move_requested_signal.emit()
        #use this to clear additional_info

class BoardGameArea(QWidget):
    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)  # Set size of the board game area
        self.game = game
        self.player = [game.player[0],game.player[1]]
        self.player[0].move_requested_signal.connect(self.clear_additional_info)
        self.player[1].move_requested_signal.connect(self.clear_additional_info)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.draw_pieces(painter)
        self.draw_valid_moves(painter)
        if(hasattr(self,"additional_info") and self.additional_info != None):
            self.draw_additional_info(painter)
    def draw_pieces(self,painter):
        for i in range(11):
            for k in range(17):
                if self.game.position.pieces[0][i][k]:
                    self.draw_piece(i,k,playerColor[self.game.active_player],painter)
                if self.game.position.pieces[1][i][k]:
                    self.draw_piece(i,k,playerColor[1-self.game.active_player],painter)
    def draw_valid_moves(self,painter):
        for i in range(11):
            for k in range(17):
                if self.game.position.valid_moves[i][k]:
                    self.draw_valid_move(i,k,painter)
    def draw_additional_info(self,painter):
        for i in range(11):
            for k in range(17):
                if (i,k) in self.additional_info.children:
                    count = self.additional_info.children[(i,k)].visit_count
                    val = -self.additional_info.children[(i,k)].value
                    self.draw_info(i,k,"{},{:.2f}".format(count,val),painter)
    def grid_size(self):
        gridX=self.width() // 11
        gridY=self.height() // 9
        grid_size = min(gridX,gridY)
        return grid_size
    def draw_valid_move(self,i,k,painter):
        grid_size=self.grid_size()
        offX=(self.width()-11*grid_size)//2
        offY=(self.height()+9*grid_size)//2
        j = k//2
        horizontal = (k%2==0)
        if(horizontal):
            posX=offX + (1+i)*grid_size
            posY=offY - int((0.5+j)*grid_size)
        else:
            posX=offX + int((0.5+i)*grid_size)
            posY=offY - (1+j)*grid_size
        painter.setBrush(dotColor)
        painter.setPen(QColor(0,0,0,0))
        if horizontal:
            painter.drawRect(posX-2*radius, posY-radius, 4*radius, 2*radius)
        else:
            painter.drawRect(posX-radius, posY-2*radius, 2*radius, 4*radius)
    def draw_piece(self,i,k,c,painter):
        grid_size=self.grid_size()
        offX=(self.width()-11*grid_size)//2
        offY=(self.height()+9*grid_size)//2
        j = k//2
        painter.setBrush(c)
        horizontal=(k%2==0)
        if(horizontal):
            painter.drawRect(offX+i*grid_size,offY-(j+1)*grid_size, 2*grid_size,grid_size)
        else:
            painter.drawRect(offX+i*grid_size,offY-(j+2)*grid_size, grid_size,2*grid_size)
    def draw_info(self,i,k,string,painter):
        grid_size=self.grid_size()
        offX=(self.width()-11*grid_size)//2
        offY=(self.height()+9*grid_size)//2
        j = k//2
        horizontal = (k%2==0)
        if(horizontal):
            posX=offX + (1+i)*grid_size
            posY=offY - int((0.5+j)*grid_size)
        else:
            posX=offX + int((0.5+i)*grid_size)
            posY=offY - (1+j)*grid_size
        painter.setPen(textColor)
        painter.drawText(posX, posY, string)

    def mousePressEvent(self,event):
        grid_size=self.grid_size()
        offX=(self.width()-11*grid_size)//2
        offY=(self.height()+9*grid_size)//2
        mouse_x = int(event.position().x())
        mouse_y = int(event.position().y())
        dot1 = ((mouse_x-offX) - (mouse_y-offY))//grid_size
        dot2 = (-(mouse_x-offX) - (mouse_y-offY))//grid_size
        k = dot1 + dot2
        i = (dot1 - dot2 - 1) // 2
        j = k//2
        horizontal = (k % 2 == 0)
        if(horizontal):
            posX=offX + (1+i)*grid_size
            posY=offY - int((0.5+j)*grid_size)
        else:
            posX=offX + int((0.5+i)*grid_size)
            posY=offY - (1+j)*grid_size
        player=self.player[self.game.active_player]
        if horizontal and abs(posX-mouse_x) <= 2*click_radius and abs(posY-mouse_y) <=click_radius:
            player.move_signal.emit(i,k)
        if not horizontal and abs(posX-mouse_x) <=click_radius and abs(posY-mouse_y) <= 2*click_radius:
            player.move_signal.emit(i,k)
    def get_additional_info(self,info):
        #currently this is always the root of an MCTS tree
        self.additional_info = info
        self.update()
    def clear_additional_info(self):
        self.additional_info = None
        self.update()
        

class InfoArea(QWidget):
    def __init__(self, game, args, board_game_area, parent=None):
        super().__init__(parent)

        self.game = game
        self.board_game_area = board_game_area

        layout = QVBoxLayout()
        self.info_label = QLabel("", self)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button = QPushButton("Restart",self)
        self.button.clicked.connect(self.restart)

        self.checkbox = QCheckBox("Autorestart")

        self.combo_box = [QComboBox(self),QComboBox(self)]
        if(args.p0 == None and args.p1 == None):
            self.combo_box[0].addItems(["Player", "AI (random)", "AI (MCTS)"])
            self.combo_box[1].addItems(["Player", "AI (random)", "AI (MCTS)"])
            self.player = [[self.game.player[0], AIPlayer(AIRandom()), AIPlayer(AI_MCTS())], [self.game.player[1], AIPlayer(AIRandom()), AIPlayer(AI_MCTS())]]
        else: #explicit player arguments provided
            self.player = [[],[]]
            if(args.p0 == None):
                self.combo_box[0].addItems(["Player"])
                self.player[0].append(self.game.player[0])
            else:
                ai = AIPlayer(AI_MCTS(path=args.p0,initialize=args.initialize, training=args.learn))
                self.combo_box[0].addItems(["AI {}".format(args.p0)])
                self.player[0].append(ai)
                self.game.connectPlayer(0, ai)
                ai.additional_info_signal.connect(self.board_game_area.get_additional_info)
            if(args.p1 == None):
                self.combo_box[1].addItems(["Player"])
                self.player[1].append(self.game.player[1])
            else:
                ai = AIPlayer(AI_MCTS(path=args.p1,initialize=args.initialize, training=args.learn))
                self.combo_box[1].addItems(["AI {}".format(args.p1)])
                self.player[1].append(ai)
                self.game.connectPlayer(1, ai)
                ai.additional_info_signal.connect(self.board_game_area.get_additional_info)
            self.combo_box[0].setEnabled(False)
            self.combo_box[1].setEnabled(False)
        self.combo_box[0].currentTextChanged.connect(self.combo0changed)
        self.combo_box[1].currentTextChanged.connect(self.combo1changed)
        layout.addWidget(self.info_label)
        layout.addWidget(self.combo_box[0])
        layout.addWidget(self.combo_box[1])
        layout.addWidget(self.button)
        layout.addWidget(self.checkbox)
        self.setLayout(layout)
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)
    def combo0changed(self):
        self.combochanged(0)
    def combo1changed(self):
        self.combochanged(1)
    def combochanged(self,index):
        combo_index = self.combo_box[index].currentIndex()
        self.game.connectPlayer(index, self.player[index][combo_index])
        if combo_index == 2:
            self.player[index][combo_index].additional_info_signal.connect(self.boardgame_area.get_additional_info)
    def restart(self):
        self.info_label.setText("")
        self.game.restart()
    def autorestart(self):
        if(self.checkbox.isChecked()):
            self.restart()
    def show_result(self,winner):
        if(winner==None):
            text="Draw!"
        else:
            text="Player {} wins!".format(winner)
        print(text)
        self.info_label.setText(text)
        self.autorestart()


class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        self.setWindowTitle("Blocks")

        players=[Player(), Player()] #slots for human interaction

        self.game = Game(players[0], players[1])

        # Create the central widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # Board game area (left side)
        self.board_game_area = BoardGameArea(self.game)

        # Info area (right side)
        self.info_area = InfoArea(self.game,args,self.board_game_area)

        self.board_game_area.info_area = self.info_area

        main_layout.addWidget(self.board_game_area)
        main_layout.addWidget(self.info_area)

        self.game.update_signal.connect(self.board_game_area.update)
        self.game.end_signal.connect(self.info_area.show_result)

        # Set the central widget for the main window
        self.setCentralWidget(central_widget)
        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--p0', type=str, help='Player 0 model path (leave empty for manual)')
    parser.add_argument('--p1', type=str, help='Player 1 model path (leave empty for manual)')
    parser.add_argument('--initialize', help='Initialize nonexistent filepaths.', action='store_true')
    parser.add_argument('--learn', help='Store experience.', action='store_true')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    window = MainWindow(args)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

