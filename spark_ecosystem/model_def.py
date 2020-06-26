import copy
import os
from typing import Any, Dict, Sequence, Union

import torch
import torchvision
from torch import nn
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
import numpy as np

import determined as det
from determined.pytorch import DataLoader, LRScheduler, PyTorchTrial
from determined.experimental import Determined

from data import VOCDeltaDataset, download_version, collate_fn
from utils import get_batch_statistics, ap_per_class

TorchData = Union[Dict[str, torch.Tensor], Sequence[torch.Tensor], torch.Tensor]


class ObjectDetectionModel(PyTorchTrial):
    def __init__(self, context: det.TrialContext) -> None:
        self.context = context
        self.current_step = context.env.first_step()

        self.download_directory = f"/tmp/data-rank{self.context.distributed.get_rank()}/"
        if "INFERENCE" in os.environ and os.environ["INFERENCE"] == "True":
            self.num_classes = 20
        else:
            self.download_data()
            self.train_dataset = VOCDeltaDataset(self.train_data_path)
            self.val_dataset = VOCDeltaDataset(self.val_data_path)
            self.num_classes = self.train_dataset.NUM_CLASSES

    def download_data(self):
        data_config = self.context.get_data_config()
        bucket = data_config['bucket']
        train_table = data_config['train']['table']
        train_version = data_config['train']['version']
        val_table = data_config['val']['table']
        val_version = data_config['val']['version']
        self.train_data_path = download_version(train_table, bucket, train_version, self.download_directory)
        self.val_data_path = download_version(val_table, bucket, val_version, self.download_directory)

    def build_training_data_loader(self) -> DataLoader:
        return DataLoader(
            self.train_dataset,
            batch_size=self.context.get_per_slot_batch_size(),
            collate_fn=collate_fn,
        )

    def build_validation_data_loader(self) -> DataLoader:
        return DataLoader(
            self.val_dataset,
            batch_size=self.context.get_per_slot_batch_size(),
            collate_fn=collate_fn,
        )

    def build_model(self) -> nn.Module:
        model = fasterrcnn_resnet50_fpn(pretrained=False, pretrained_backbone=False)

        # Replace the classifier with a new two-class classifier.  There are
        # only two "classes": pedestrian and background.
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, self.num_classes)
        load_exp = self.context.get_hparam("load_from_experiment")
        if load_exp > 0:
            os.environ["INFERENCE"] = "True"
            pretrained = Determined().get_experiment(load_exp).top_checkpoint().load(path=self.download_directory)
            os.environ["INFERENCE"] = "False"
            model.load_state_dict(pretrained.state_dict())
        return model

    def optimizer(self, model: nn.Module) -> torch.optim.Optimizer:
        optimizer = torch.optim.SGD(
            model.parameters(),
            lr=self.context.get_hparam("learning_rate"),
            momentum=self.context.get_hparam("momentum"),
            weight_decay=self.context.get_hparam("weight_decay"),
        )
        return optimizer

    def create_lr_scheduler(self, optimizer):
        lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[8, 12], gamma=0.1)
        # lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)
        return LRScheduler(lr_scheduler, step_mode=LRScheduler.StepMode.STEP_EVERY_EPOCH)

    def train_batch(
        self, batch: TorchData, model: nn.Module, epoch_idx: int, batch_idx: int
    ) -> Dict[str, torch.Tensor]:
        images, targets = batch
        loss_dict = model(list(images), list(targets))
        total_loss = sum([loss_dict[l] for l in loss_dict])

        # Set current step based on 100 batches / step
        self.current_step = batch_idx // 20

        return {"loss": total_loss}


    def evaluate_full_dataset(self, data_loader, model):
        batch_stats = []
        model.eval()
        device = torch.device('cuda')
        with torch.no_grad():
            for images, targets in data_loader:
                images = list(images)
                targets = list(targets)
                # for image in images:
                #     image = image.to(device)
                # for target in targets:
                #     target['labels'] = target['labels'].to(device)
                #     target['boxes'] = target['boxes'].to(device)
                outputs = model(images, copy.deepcopy(targets))
                batch_stats += get_batch_statistics(outputs, targets, iou_threshold=0.5)

        true_positives, pred_scores, pred_labels, labels = [np.concatenate(x, 0) for x in list(zip(*batch_stats))]
        precision, recall, AP, f1, ap_class = ap_per_class(true_positives, pred_scores, pred_labels, labels)
        metrics =  {'mAP': AP.mean()}
        for i, c in enumerate(ap_class):
            class_name = self.train_dataset.number2name[c]
            metrics[f'AP_{class_name}'] = AP[i]
        return metrics

    # def evaluate_batch(self, batch: TorchData, model: nn.Module) -> Dict[str, Any]:
    #     images, targets = batch
    #     outputs = model(list(images), copy.deepcopy(list(targets)))
    #     batch_stats = get_batch_statistics(outputs, targets, iou_threshold=0.5)
    #     true_positives, pred_scores, pred_labels, labels = [np.concatenate(x, 0) for x in list(zip(*batch_stats))]
    #     precision, recall, AP, f1, ap_class = ap_per_class(true_positives, pred_scores, pred_labels, labels)
    #     metrics =  {'mAP': AP.mean()}
    #     for i, c in enumerate(ap_class):
    #         metrics[f'AP_class{c}'] = AP[i]
    #     return metrics
