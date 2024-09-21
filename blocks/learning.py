from mcts import VPFunction

import torch
import torch.nn as nn

from pathlib import Path

class PolicyNet(nn.Module):
        # Run superclass constructor to get all the  `nn.Module` magic
    def __init__(self,path,initialize=False):
        super().__init__()
        # Define some layers; this can get more complicated later
        self.layers = nn.Sequential(
            nn.Linear(2 * 11 * 17, 256),
            nn.LeakyReLU(),
            nn.Linear(256, 256),
            nn.LeakyReLU(),
            nn.Linear(256, 11 * 17 + 1),  
            # Note: no final activation here!
        )
        if not initialize:
            self.load(path)
        else:
            self.save(path)
    def forward(
            self, 
            x: torch.Tensor, 
            y: torch.Tensor,
        ) -> tuple[torch.Tensor, torch.Tensor]:
            """
            Args:
                x: (batch_size, 11, 17)
                y: (batch_size, 11, 17)
            """
            # Flatten and concatenate the inputs
            # This should have shape (batch_dimension, 2 * 11 * 17)
            # In a later step, we can start using conv layers here instead
            foo = torch.concatenate(
                [
                    x.reshape(-1, 11 * 17),
                    y.reshape(-1, 11 * 17),
                ],
                dim=1,
            )
    
            # Pass this through the feed-forward part
            foo = self.layers(foo)
    
            # Split into two parts
            value = foo[:, 0]  # shape: (batch_dimension, 1)
            policy = foo[:, 1:]  # shape: (batch_dimension, 11 * 17)
    
            # Reshape policy back to 2D
            policy = policy.reshape(-1, 11, 17)
    
            # Normalize
            value = 2 * (torch.sigmoid(value) - 0.5)  # in [-1, 1]
            policy = torch.sigmoid(policy)  # in [0, 1]
            return value, policy
    def save(self,path):
        torch.save(self.state_dict(), path)
    def load(self,path):
        self.load_state_dict(torch.load(path))
    def train(self,path_to_games_dir):
        path = Path(path_to_games_dir)
        x_as_list=[]
        y_as_list=[]
        v_as_list=[]
        p_as_list=[]
        for file_path in path.glob("*.exp"):
            game_experience=np.load(file_path)
            x_as_list.append(game["player0"])
            y_as_list.append(game["player1"])
            v_as_list.append(game["target_value"])
            p_as_list.append(game["target_policy"])
        x_as_np = np.concatenate(x_as_list, axis=0)
        y_as_np = np.concatenate(y_as_list, axis=0)
        v_as_np = np.concatenate(v_as_list, axis=0)
        p_as_np = np.concatenate(p_as_list, axis=0)


class NN_VPFunction(VPFunction):
    def __init__(self,path,initialize=False):
        super().__init__()
        self.policy_net=PolicyNet(path,initialize)

    def compute(self,position):
        pieces0 = position.pieces[0]
        pieces1 = position.pieces[1]
        x = torch.from_numpy(pieces0).float()
        y = torch.from_numpy(pieces1).float()
        value,policy = self.policy_net(x,y)
        #mask and normalize
        policy = policy[0].detach().numpy() * position.valid_moves
        policy = policy / policy.sum() 
        return (value[0],policy)

        #target = torch.randn(11, 17)
        #loss = nn.functional.mse_loss(policy, target)
        #loss.backward()
        #print(next(policy_net.parameters()).grad)


