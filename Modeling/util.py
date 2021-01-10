import torch

def mase_loss(output, label):
    return torch.mean(torch.abs(output - label)) / torch.mean(label)