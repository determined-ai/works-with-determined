import os
from typing import Any, Dict, Sequence, Tuple, Union, cast
import logging

import torch
from torch import nn
from determined.pytorch import DataLoader, PyTorchTrial
from torchvision import models, transforms
import numpy as np
from PIL import Image

from data import CatDogDataset, download_pach_repo
TorchData = Union[Dict[str, torch.Tensor], Sequence[torch.Tensor], torch.Tensor]

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# =============================================================================

class DogCatModel(PyTorchTrial):
    def __init__(self, context):
        self.context = context
        self.download_directory = f"/tmp/data-rank{self.context.distributed.get_rank()}"

        load_weights = (os.environ.get('SERVING_MODE') != 'true')
        logging.info(f"Loading weights : {load_weights}")

        if load_weights:
            self.data_dir = self.download_data()

        model = models.resnet50(pretrained=load_weights)
        model.fc = nn.Linear(2048, 2)
        optimizer = torch.optim.SGD(model.parameters(),
                                    lr=float(self.context.get_hparam("learning_rate")),
                                    momentum=0.9,
                                    weight_decay=float(self.context.get_hparam("weight_decay")),
                                    nesterov=self.context.get_hparam("nesterov"))

        self.model = self.context.wrap_model(model)
        self.optimizer = self.context.wrap_optimizer(optimizer)
        self.labels = ['dog', 'cat']

    # -------------------------------------------------------------------------

    def train_batch(self, batch: TorchData, epoch_idx: int, batch_idx: int) -> Union[torch.Tensor, Dict[str, Any]]:
        batch = cast(Tuple[torch.Tensor, torch.Tensor], batch)
        data, labels = batch

        output = self.model(data)
        loss = torch.nn.functional.cross_entropy(output, labels)

        self.context.backward(loss)
        self.context.step_optimizer(self.optimizer)

        return {"loss": loss}

    # -------------------------------------------------------------------------

    def evaluate_batch(self, batch: TorchData, batch_idx: int) -> Dict[str, Any]:
        """
        Calculate validation metrics for a batch and return them as a dictionary.
        This method is not necessary if the user overwrites evaluate_full_dataset().
        """
        batch = cast(Tuple[torch.Tensor, torch.Tensor], batch)
        data, labels = batch
        output = self.model(data)

        pred = output.argmax(dim=1, keepdim=True)
        accuracy = pred.eq(labels.view_as(pred)).sum().item() / len(data)
        return {"accuracy": accuracy}

    # -------------------------------------------------------------------------

    def build_training_data_loader(self) -> DataLoader:
        ds = CatDogDataset(self.data_dir, train=True, transform=self.get_train_transforms())
        return DataLoader(ds, batch_size=self.context.get_per_slot_batch_size())

    # -------------------------------------------------------------------------

    def build_validation_data_loader(self) -> DataLoader:
        ds = CatDogDataset(self.data_dir, train=False, transform=self.get_test_transforms())
        return DataLoader(ds, batch_size=self.context.get_per_slot_batch_size())

    # -------------------------------------------------------------------------

    def download_data(self) -> str:
        data_config = self.context.get_data_config()
        data_dir = os.path.join(self.download_directory, 'data')
        pachyderm_host = data_config['pachyderm']['host']
        pachyderm_port = data_config['pachyderm']['port']

        download_pach_repo(
            pachyderm_host,
            pachyderm_port,
            data_config["pachyderm"]["repo"],
            data_config["pachyderm"]["branch"],
            data_dir,
            data_config["pachyderm"]["token"]
        )
        print(f'Data dir set to : {data_dir}')
        return data_dir

    # -------------------------------------------------------------------------

    def get_train_transforms(self):
        return transforms.Compose([
            transforms.Resize(240),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])

    # -------------------------------------------------------------------------

    def get_test_transforms(self):
        return transforms.Compose([
            transforms.Resize(240),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])

    # -------------------------------------------------------------------------

    def predict(self, image: Image):
        image = self.get_test_transforms()(image)
        image = image.unsqueeze(0)

        with torch.no_grad():
            output = self.model(image)[0]
            pred = np.argmax(output)
            logging.info(f"Prediction is : {pred}")

        return [self.labels[pred]]

# =============================================================================
