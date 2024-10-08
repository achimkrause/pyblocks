from position import Position

import numpy as np
import random as rnd

c = 1.4


def playout(position):
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
    if(active_player == 0):
        return pos.result
    else:
        return 1.0 - pos.result

#default value and policy function, single random full playout
class VPFunction:
    def __init__(self):
        pass
    def compute(self,position):
        value = playout(position)
        policy = np.zeros(shape=(11,17))
        movecount = 0.0
        for i in range(11):
            for k in range(17):
                if position.valid_moves[i][k]:
                    policy[i][k]=1.0
                    movecount += 1.0
        if movecount > 0.0:
            policy = policy / movecount
        return (value,policy)

#posterior value, posterior policy (temp 1)
class Experience:
    def __init__(self, position, posterior_policy):
        self.player0_pieces = position.pieces[0]
        self.player1_pieces = position.pieces[1]
        self.posterior_policy = posterior_policy
    #posterior value gets added later when game is finished

class MCTSTree:
    def __init__(self, vp_function, position, root=False):
        self.position = position
        self.vp_function = vp_function
        self.prior_value, self.prior_policy = self.vp_function.compute(self.position)
        if(root):
            count_valid_moves = 0
            for i in range(11):
                for k in range(17):
                    if position.valid_moves[i][k]:
                        count_valid_moves += 1
            #add noise to prior_policy
            noise_arr = 0.25 * np.random.dirichlet(np.full(fill_value=0.2,shape=(count_valid_moves)))
            count = 0
            for i in range(11):
                for k in range(17):
                    if position.valid_moves[i][k]:
                        self.prior_policy[i][k] += noise_arr[count]
                        count += 1
            self.prior_policy = self.prior_policy / self.prior_policy.sum()



        self.value = self.prior_value
        self.visit_count = 1 #N
        self.children = {}
        #if we explore move (i,k), we add a new child,
        #increment self.visit_count
        #add new_child.value to self.value
        #always visit the child with maximal self.children[(i,k)].q + policy[i][k] / (1 + self.children[(i,k)].n)

        #once done, the policy is computed as the vector
        # children.n^(1/tau), normalized to sum 1.
    def action_value(self): #Q
        return self.value / self.visit_count
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

                u = c * self.prior_policy[i][k] * np.sqrt(self.visit_count - 1)/(1.0+child_n)
                if (i,k) in self.children:
                    qplusu = u + (1.0 - self.children.get((i,k)).action_value())
                else:
                    qplusu = u
                if child_qplusu==None or qplusu > child_qplusu:
                    child_i=i
                    child_k=k
                    child_qplusu=qplusu
        return (child_i,child_k) #to exclude the None,None case, we need to ensure that we call this only if the position is not decided
    def visit_child(self):
        if(self.position.over):
            v=self.position.result
            self.value += v
            self.visit_count += 1
            return v
            
        i,k = self.select_child()
        if (i,k) in self.children:
            v = 1.0-self.children[(i,k)].visit_child()
        else:
            pos = self.position.copy()
            pos.move(i,k)
            self.children[(i,k)] = MCTSTree(self.vp_function,pos)
            v = 1.0-self.children[(i,k)].value
        self.value += v
        self.visit_count += 1
        return v
    def compute_posterior_policy(self,temperature=1.0):
        policy = np.zeros(shape=(11,17))
        max_count = None
        for i in range(11):
            for k in range(17):
                if (i,k) in self.children:
                    visit_count = self.children[(i,k)].visit_count
                    policy[i][k]=visit_count
                    if max_count == None or visit_count > max_count:
                        max_count = visit_count
        #print(policy / policy.sum())
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
    def compute_experience(self):
        posterior_policy = self.compute_posterior_policy(1.0)
        exp = Experience(self.position, posterior_policy)
        return exp
    def debug(self):
        for i in range(11):
            for k in range(17):
                if not self.position.valid_moves[i][k]:
                    continue
                visit_count=0
                if (i,k) in self.children:
                    visit_count = self.children[(i,k)].visit_count
                print(f"({i},{k}): visit_count {visit_count}, policy {self.prior_policy[i][k]}")













