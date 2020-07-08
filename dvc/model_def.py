import os
import tarfile
from typing import Any, Dict, Sequence, Tuple, Union, cast

import torch
import torchvision
from torch import nn
from determined.pytorch import DataLoader, PyTorchTrial, reset_parameters
from torchvision import models, transforms
from tqdm import tqdm


from data import CatDogDataset, get_test_transforms
TorchData = Union[Dict[str, torch.Tensor], Sequence[torch.Tensor], torch.Tensor]


class CatDogModel(PyTorchTrial):
    def __init__(self, context):
        self.context = context
        self.data_dir = "images/"
        self.test_transform = get_test_transforms()

    def build_model(self) -> nn.Module:
        model = models.resnet50(pretrained=True)
        model.fc = nn.Linear(2048, 2)
        return model

    def optimizer(self, model: nn.Module) -> torch.optim.Optimizer:  # type: ignore
        return torch.optim.SGD(model.parameters(),
                               lr=float(self.context.get_hparam("learning_rate")),
                               momentum=0.9,
                               weight_decay=float(self.context.get_hparam("weight_decay")),
                               nesterov=self.context.get_hparam("nesterov"))

    def train_batch(
        self, batch: TorchData, model: nn.Module, epoch_idx: int, batch_idx: int
    ) -> Dict[str, torch.Tensor]:
        batch = cast(Tuple[torch.Tensor, torch.Tensor], batch)
        data, labels = batch

        output = model(data)
        loss = torch.nn.functional.cross_entropy(output, labels)
        return {"loss": loss}

    def evaluate_batch(self, batch: TorchData, model: nn.Module) -> Dict[str, Any]:
        """
        Calculate validation metrics for a batch and return them as a dictionary.
        This method is not necessary if the user overwrites evaluate_full_dataset().
        """
        batch = cast(Tuple[torch.Tensor, torch.Tensor], batch)
        data, labels = batch

        output = model(data)
        pred = output.argmax(dim=1, keepdim=True)
        accuracy = pred.eq(labels.view_as(pred)).sum().item() / len(data)
        return {"accuracy": accuracy}

    def build_train_dataset(self):
        transform = transforms.Compose([
            transforms.Resize(240),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])
        ds = CatDogDataset(self.data_dir, train=True, transform=transform)
        return ds

    def build_test_dataset(self):
        ds = CatDogDataset(self.data_dir, train=False, transform=self.test_transform)
        return ds

    def build_training_data_loader(self) -> Any:
        ds = self.build_train_dataset()
        return DataLoader(ds, batch_size=self.context.get_per_slot_batch_size())

    def build_validation_data_loader(self) -> Any:
        ds = self.build_test_dataset()
        return DataLoader(ds, batch_size=self.context.get_per_slot_batch_size())
