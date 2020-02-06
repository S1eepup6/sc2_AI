import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical

import os

#Hyperparameters
learning_rate = 0.005

class net(nn.Module):
    def __init__(self):
        super(net, self).__init__()
        self.data = []
        self.result = []
        self.answer = []

        self.fc1    = nn.Linear(5, 256)
        self.fc2    = nn.Linear(256, 128)
        self.fc_pi  = nn.Linear(128,  1)
        self.fc_v   = nn.Linear(128,  1)
        self.optimizer = optim.SGD(self.parameters(), lr=learning_rate, momentum=0.9)
        self.criterion = nn.MSELoss()

    def forward(self, x):
        x = self.fc1(x)
        x = self.fc2(x)
        x = torch.sigmoid(self.fc_pi(x))
        return x