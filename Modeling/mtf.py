import datetime
import pickle
import torch
from typing import *
from matplotlib import pyplot as plt
import numpy as np
from copy import deepcopy

class Timestamp(datetime.datetime):
    """
    Timestamp class, datetime.datetime remade in case there are future convenience modifications to make.
    """
    def __init__(self, dt: datetime.datetime):
        super(Timestamp, self).__init__(dt.year, dt.month, dt.day)

class Snapshot:
    """
    Individual data snapshots that are passed through the datastream
    Represented as a timestamp and JSON formatted data
    """
    def __init__(self, timestamp: Timestamp, data: object):
        self.timestamp = timestamp
        self.data = data

class DataTransformer:
    """
    Converts incoming data into Datastream of form to be used for training and analysis.
    """

class Datastream:
    """
    List of Snapshots
    """
    def __init__(self, items: list=[]):
        self.items = items
        self.index = 0

    # @property
    # def start_timestamp(self):
    #     if len(self.items):
    #         self.start_timestamp = self.items[0].timestamp
    #     else:
    #         self.start_timestamp = Timestamp.now()

    # @property
    # def current_timestamp(self):
    #     if len(self.items):
    #         self.current_timestamp = self.items[-1].timestamp
    #     else:
    #         self.current_timestamp = Timestamp.now()

    @property
    def length(self):
        return len(self.items)

    def save(self):
        """
        Save a representation of this object to a file for later use with pickle
        """
        pass

    def __getitem__(self, key):
        return self.items[key]

    def __next__(self):
        item = self.items[self.index]
        self.index += 1
        return item

    def train_split(self, train_portion: float=0.8):
        sample = self.length
        train_length = int(train_portion * sample)
        val_length = int(sample * (1.0 - train_portion) / 2.0)

        train_datastream = deepcopy(self)
        train_datastream.items = train_datastream.items[:train_length]
        val_datastream = deepcopy(self)
        val_datastream.items = val_datastream.items[train_length:train_length + val_length]
        test_datastream = deepcopy(self)
        test_datastream.items = test_datastream.items[train_length + val_length:]

        return train_datastream, val_datastream, test_datastream

    def data_split(self, begin: Timestamp=None, end: Timestamp=None):
        """
        Create a copy Datastream including only Snapshots between begin and end.
        """
        if begin is None:
            begin = self.start_timestamp
        if end is None:
            end = self.items[-1].timestamp

        assert begin <= end, "begin must be before end"

        begin_index = 0
        for i in range(len(self.items)):
            timestamp = self.items[i].timestamp
            if timestamp >= begin:
                begin_index = i
                break

        end_index = begin_index
        for i in range(begin_index, len(self.items)):
            timestamp = self.items[i].timestamp
            if timestamp >= end:
                end_index = i
                break

        return Datastream(items=self.items[begin_index : end_index + 1])

class Datum:
    """
    A series of feature snapshots and a series of label snapshots.
    """
    def __init__(self, x: list, y: list):
        self.x = torch.FloatTensor([[a] for a in x])
        self.y = torch.FloatTensor([[a] for a in y])

class Data(Datastream):
    """
    This class is Datastream except the items are of the Datum class rather than Snapshot
    Class contains methods for constructing special lookback sequences from a Datastream.
    """
    def __init__(self, items: list, lookback_pattern: list=[5, 4, 3, 2, 1], y_pattern: list=[0]):
        self.index = 0

        lookback_pattern.sort(reverse=True)
        y_pattern.sort()
        self.lookback_pattern = lookback_pattern
        self.y_pattern = y_pattern
        self.items = []
        #TODO: Change the range so that lookback on first example is snapshots[0] and y_pattern[-1] is snapshots[-1] on the last example. Right now first x[0] is a negative number
        for i in range(len(items) - lookback_pattern[0] - y_pattern[-1]):
            x, y = [], []
            for lookback in lookback_pattern:
                x.append(items[i - lookback])
            for lookforward in y_pattern:
                y.append(items[i + lookforward])
            datum = Datum(x, y)
            self.items.append(datum)

class Trainer:
    """
    Class for training, validating, and testing a forecasting model.
    """
    def __init__(self, model: torch.nn.Module, data: Data, optimizer: torch.optim.Optimizer, loss_func: Callable):
        self.model = model
        self.data = data
        self.optimizer = optimizer
        self.loss_func = loss_func

    def forward(self, data: Data, train=True, h=None, c=None, reset_states=False):
        predictions = []
        labels = []

        if train:
            self.model.train()
        else:
            self.model.eval()

        cost = 0
        for i in range(data.length):
            if reset_states:
                h, c = None, None
            datum = data[i]
            for j in range(len(datum.x)):
                y_hat, h, c = self.model(datum.x[j], h, c)
                if not train:
                    y_hat, h, c = y_hat.detach(), h.detach(), c.detach()
            predictions.append(y_hat)
            labels.append(datum.y)
            cost += self.loss_func(y_hat, datum.y)
        if train:
            cost /= i + 1
            cost.backward()
            self.optimizer.step()
            self.optimizer.zero_grad()
        
        return predictions, labels, cost, h, c

    def train(self, num_epochs: int=20, batch_size: int=None, train_portion: float=0.8, display_losses: bool=True, display_predictions: bool=True):

        #TODO: Batch size
        if batch_size is None:
            batch_size = self.data.length

        train, val, test = self.data.train_split(train_portion)

        train_losses, val_losses, test_losses = [], [], []

        for epoch in range(num_epochs):

            predictions = []
            labels = []

            prediction, label, cost, h, c = self.forward(train)
            predictions += prediction
            labels += label
            train_losses.append(cost)

            with torch.no_grad():
                prediction, label, cost, h, c = self.forward(val, train=False, h=h, c=c)
                predictions += prediction
                labels += label
                val_losses.append(cost)

                prediction, label, cost, _, _ = self.forward(test, train=False, h=h, c=c)
                predictions += prediction
                labels += label
                test_losses.append(cost)

            if display_losses:
                # Display losses for this epoch
                print('Epoch: {:03d}, Train Loss: {:.5f}, Val Loss: {:.5f}, Test Loss: {:.5f}'.format(epoch, train_losses[-1], val_losses[-1], test_losses[-1]))
            if display_predictions and epoch == num_epochs - 1:
                plot_predictions(predictions, labels)

        return train_losses, val_losses, test_losses


def plot_losses(train_losses: list, val_losses: list, test_losses: list):
    num_epochs = len(train_losses)

    # Set labels and plot loss curves for validation
    x = np.arange(0, num_epochs)
    plt.title('Title')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss Probably')
    plt.plot(x, train_losses, label="Training Loss")
    plt.plot(x, val_losses, label="Validation Loss")
    plt.plot(x, test_losses, label="Testing Loss")
    plt.legend()
    plt.show()

def plot_comparison(model_losseses: list):
    """Compare the loss curves of a series of models"""
    pass

def plot_predictions(predictions, labels):
    # Plot predictions and labels over time
    x = np.arange(0, len(predictions))
    plt.title('Predictions')
    plt.xlabel("Time")
    plt.ylabel("Prediction")
    plt.plot(x, [torch.mean(p) for p in predictions], label="Predictions")
    plt.plot(x, [torch.mean(l) for l in labels], label="Labels")
    plt.legend()
    plt.show()
        

class Strategy:
    """
    Strategies convert the outcome of a model into planned trading actions
    """

class Executor:
    """
    Converts strategy into scheduled trading actions
    """

class BacktestExecutor(Executor):
    """
    Get the results of executing a trading strategy on past data; paper trading
    """