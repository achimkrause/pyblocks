import random as rnd

from ai import AI, AITemplate

class AIRandomTemplate(AITemplate):
    def __init__(self):
        super().__init__()
    def new(self):
        return AIRandom()

class AIRandom(AI):
    def __init__(self):
        super().__init__()
    def find_move(self,position):
        count=0
        for i in range(11):
            for k in range(17):
                if position.valid_moves[i][k]:
                    count +=1
        val=rnd.randint(0,count-1)
        for i in range(11):
            for k in range(17):
                if position.valid_moves[i][k]:
                    val-=1
                    if val<0:
                        return (i,k)
