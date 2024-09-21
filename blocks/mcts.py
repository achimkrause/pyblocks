from position import Position

import numpy as np
import random as rnd

c = 1.4

def rollout(position):
    pos = position.copy()
    active_player = 0
    while(not pos.over):
        count=0
        for i in range(11):
            for k in range(17):
                if pos.valid_moves[i][k]:
                    count +=1
        val=rnd.randint(0,count-1)
        for i in range(11):
            for k in range(17):
                if pos.valid_moves[i][k]:
                    val-=1
                    if val<0:
                        pos.move(i,k)
                        active_player = 1-active_player
    #result 0 means draw
    if(pos.result == 0):
        return 0
    #result 1 means the player who last moved won. This is the opposite of active player since we swapped.
    if(pos.result == 1 and active_player==1):
        return 1
    if(pos.result == 1 and active_player==0):
        return -1


class MCTSTree:
    def __init__(self, position):
        self.position = position
        self.value = self.compute_value()
        self.visit_count = 1 #N
        self.children = {}
        self.policy = self.compute_prior_policy()
        #if we explore move (i,k), we add a new child,
        #increment self.visit_count
        #add new_child.value to self.value
        #always visit the child with maximal self.children[(i,k)].q + policy[i][k] / (1 + self.children[(i,k)].n)

        #once done, the policy is computed as the vector
        # children.n^(1/tau), normalized to sum 1.
    def action_value(self): #Q
        return self.value / self.visit_count
    def compute_value(self): #this will be learned, in the basic version it is given by the random rollout
        return rollout(self.position)
    def compute_prior_policy(self): #this will be learned, here it is just uniform
        policy = np.zeros(shape=(11,17))
        movecount = 0.0
        for i in range(11):
            for k in range(17):
                if self.position.valid_moves[i][k]:
                    policy[i][k]=1.0
                    movecount += 1.0
        if movecount > 0.0:
            policy = policy / movecount
        return policy
    def select_child(self):
        child_i = None
        child_k = None
        child_qplusu = None
        for i in range(11):
            for k in range(17):
                if self.position.valid_moves[i][k] == 0:
                    continue
                child_n = 0
                if (i,k) in self.children:
                    child_n = self.children.get((i,k)).visit_count

                u = c * self.policy[i][k] * np.sqrt(self.visit_count - 1)/(1.0+child_n)
                if (i,k) in self.children:
                    qplusu = u - self.children.get((i,k)).action_value()
                else:
                    qplusu = u
                if child_qplusu==None or qplusu > child_qplusu:
                    child_i=i
                    child_k=k
                    child_qplusu=qplusu
        return (child_i,child_k) #to exclude the None,None case, we need to ensure that we call this only if the position is not decided
    def visit_child(self):
        if(self.position.over):
            v=rollout(self.position) #this is just the result in that case
            self.value += v
            self.visit_count += 1
            return v
            
        i,k = self.select_child()
        if (i,k) in self.children:
            v = -self.children[(i,k)].visit_child()
        else:
            pos = self.position.copy()
            pos.move(i,k)
            self.children[(i,k)] = MCTSTree(pos)
            v = -self.children[(i,k)].value
        self.value += v
        self.visit_count += 1
        return v
    def compute_posterior_policy(self,temperature=0.0):
        policy = np.zeros(shape=(11,17))
        max_count = None
        for i in range(11):
            for k in range(17):
                if (i,k) in self.children:
                    visit_count = self.children[(i,k)].visit_count
                    policy[i][k]=visit_count
                    if max_count == None or visit_count > max_count:
                        max_count = visit_count
        policy = policy / max_count
        if temperature < 1e-8:
            policy = np.floor(policy)
        else:
            policy = np.log(policy)
            policy = policy / temperature
            policy = np.exp(policy)
        total = np.sum(policy)
        policy = policy / total
        return policy












