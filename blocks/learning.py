from mcts import VPFunction

import torch
import torch.nn as nn

import numpy as np

from pathlib import Path

import os

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
            nn.Linear(256, 256),
            nn.LeakyReLU(),
            nn.Linear(256, 256),
            nn.LeakyReLU(),
            nn.Linear(256, 256),
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
    
            # Normalize
            value = torch.sigmoid(value)  # in [0, 1]
            logpolicy = nn.LogSigmoid()(policy)  # in (-infty, 0]
            logpolicysum = torch.logsumexp(policy,1).reshape(-1,1).expand(-1,11*17)
            logpolicy = logpolicy - logpolicysum

            # Reshape outputs
            value = value.reshape(-1, 1)
            logpolicy = logpolicy.reshape(-1, 11, 17)
            return value, logpolicy
    def save(self,path):
        torch.save(self.state_dict(), path)
    def load(self,path):
        self.load_state_dict(torch.load(path))

class Training:
    def __init__(self,path,new_path, overwrite=False):
        self.policy_net = PolicyNet(path / 'model.weights')
        self.path_to_games = path / 'games'
        self.new_path = new_path
        if not overwrite and new_path.exists():
            raise ValueError("{} exists already!".format(new_path))

    def run(self):
        x_as_list=[]
        y_as_list=[]
        v_as_list=[]
        p_as_list=[]
        for file_path in self.path_to_games.glob("*.npz"):
            game_experience=np.load(file_path)
            x_as_list.append(game_experience["player0"])
            y_as_list.append(game_experience["player1"])
            v_as_list.append(game_experience["target_value"])
            p_as_list.append(game_experience["target_policy"])
        x_as_np = np.concatenate(x_as_list, axis=0)
        y_as_np = np.concatenate(y_as_list, axis=0)
        v_as_np = np.concatenate(v_as_list, axis=0)
        p_as_np = np.concatenate(p_as_list, axis=0)
        # Convert the game data to tensors (for PyTorch)
        dataset = torch.utils.data.TensorDataset(
            torch.from_numpy(x_as_np).float(),
            torch.from_numpy(y_as_np).float(),
            torch.from_numpy(v_as_np).float(),
            torch.from_numpy(p_as_np).float(),
        )
        # Construct a dataloader to loop over them in batches
        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=42,  # define batch size
            shuffle=True,
            num_workers=2,
        )
        print("Loaded dataset, {} entries".format(x_as_np.shape[0]))

        # Pick an optimizer and learning rate of your liking
        optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=3e-4)
        
        # Train for a given number of epochs
        for epoch in range(50):
            print("Training epoch {}".format(epoch))
            # Make sure your model is in training mode
            self.policy_net.train()
            # Loop over your dataset
            for x,y,target_v,target_p in dataloader:
                # Reset gradients
                optimizer.zero_grad()
                # Forward pass
                v,lp = self.policy_net(x,y)
                # Compute loss and gradients
                # The MSE loss is probably not a great choice here...
                loss = (
                        (v - target_v) ** 2 -  # MSE of values
                        (lp * target_p).sum((1, 2))  # CE of policies
                    ).mean()  # mean over the batche
                print(loss)
                loss.backward()
                # Take a step with the optimizer
                optimizer.step()
            # Optional: Perform a validation step to check
            # against overfitting
            #self.policy_net.eval()
            #do_validation()

        print("Creating {}".format(self.new_path))

        if not self.new_path.exists():
            self.new_path.mkdir()
        if not (self.new_path/'games').exists():
            (self.new_path/'games').mkdir()

        print("Saving new model")
        self.policy_net.save(self.new_path/'model.weights')


class NN_VPFunction(VPFunction):
    def __init__(self,path,initialize=False):
        super().__init__()
        self.policy_net=PolicyNet(path,initialize)

    def compute(self,position):
        pieces0 = position.pieces[0]
        pieces1 = position.pieces[1]
        x = torch.from_numpy(pieces0).float()
        y = torch.from_numpy(pieces1).float()
        value,logpolicy = self.policy_net(x,y)
        #mask and normalize
        logpolicy = logpolicy[0].detach().numpy()
        policy = np.exp(logpolicy) * position.valid_moves
        policy = policy / policy.sum() 
        value = value[0].detach().numpy()
        return (value[0],policy)

        #target = torch.randn(11, 17)
        #loss = nn.functional.mse_loss(policy, target)
        #loss.backward()
        #print(next(policy_net.parameters()).grad)

