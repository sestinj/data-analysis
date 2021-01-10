from db_connection import connect_postgres, query
from mtf import *
import torch
from util import mase_loss

connection, cursor = connect_postgres()
TICKER = "MSFT"
QUERY = """
SELECT * FROM financial_data WHERE stock_name='%s'
""" % (TICKER)
data = query(cursor, QUERY)

items = []

for datum in data[::14]:
    items.append(torch.FloatTensor(datum[2:3]))

data = Data(items)

class BasicModel(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, dim: int):
        super(BasicModel, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.dim = dim
        self.lstm_depth = 3


        self.prelin1 = torch.nn.Linear(in_channels, dim)
        self.preact = torch.nn.ReLU()
        self.prelin2 = torch.nn.Linear(dim, dim)
        self.lstm = torch.nn.LSTM(dim, dim, self.lstm_depth, dropout=0.25)
        self.lin1 = torch.nn.Linear(dim, dim)
        self.act1 = torch.nn.ReLU()
        self.lin2 = torch.nn.Linear(dim, out_channels)

    def forward(self, input, h=None, c=None):
        x = self.prelin1(input)
        x = self.preact(x)
        x = self.prelin2(x)

        x = x.reshape(1, 1, self.dim)

        if h is None:
            h = torch.zeros(self.lstm_depth, 1, self.dim)
        if c is None:
            c = torch.zeros(self.lstm_depth, 1, self.dim)

        for i in range(self.lstm_depth):
            x2, (h, c) = self.lstm(x, (h, c))

        x = torch.cat((x, x2), 1)

        x = self.lin1(x)
        # x = self.act1(x)
        x = self.lin2(x)
        
        return x, h, c

model = BasicModel(1, 1, 8)
optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
loss_func = mase_loss
trainer = Trainer(model, data, optimizer, loss_func)

train_losses, val_losses, test_losses = trainer.train()

plot_losses(train_losses, val_losses, test_losses)