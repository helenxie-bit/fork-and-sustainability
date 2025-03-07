from torch import nn

class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()
        input_features = 15
        self.input_layer = nn.Linear(input_features, 64)
        self.hidden_1 = nn.Linear(64, 64)
        self.hidden_2 = nn.Linear(64, 64)
        self.output_layer = nn.Linear(64, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = self.relu(self.input_layer(x))
        x = self.relu(self.hidden_1(x))
        x = self.relu(self.hidden_2(x))
        x = self.sigmoid(self.output_layer(x))
        return x