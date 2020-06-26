import copy
import os
import torch
import torchvision
import time

import numpy as np
from torch.utils.data import DataLoader
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from tqdm.auto import tqdm

from data import VOCDeltaDataset, download_version, collate_fn
from utils import get_batch_statistics, ap_per_class


class ObjectDetectionModel(object):

    def __init__(self, hparams, train_data_version=0, val_data_version=0):
        self.train_data_version = train_data_version
        self.val_data_version = val_data_version
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.hparams = hparams

        self.download_directory = "/tmp/VOC/"
        self.build_model()
        self.make_data_loaders()
        self.make_optimizer()
        self.epoch = 0

    def build_model(self):
        model = fasterrcnn_resnet50_fpn(pretrained=False)
        num_classes = 20
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        self.model = model.to(self.device)

    def make_data_loaders(self):
        self._download_data()
        self.train_dataset = VOCDeltaDataset(self.train_data_path)
        self.val_dataset = VOCDeltaDataset(self.val_data_path)
        self.train_loader = DataLoader(self.train_dataset, batch_size=4, collate_fn=collate_fn, shuffle=True)
        self.val_loader = DataLoader(self.val_dataset, batch_size=4, collate_fn=collate_fn, shuffle=False)

    def make_optimizer(self):
        self.optimizer = torch.optim.SGD(
                self.model.parameters(),
                lr=self.hparams['lr'],
                momentum=self.hparams['m'],
                weight_decay=.0005,
            )

    def _download_data(self):
        bucket = 'david-voc-delta'
        train_table = 'train'
        train_version = self.train_data_version
        val_table = 'val'
        val_version = self.val_data_version
        self.train_data_path = download_version(train_table, bucket, train_version, self.download_directory)
        self.val_data_path = download_version(val_table, bucket, val_version, self.download_directory)

    def train_one_epoch(self):
        self.model.train();
        self.optimizer.zero_grad()
        self.epoch += 1
        train_loop = tqdm(self.train_loader, desc=f"Training Epoch {self.epoch}")
        for images, targets in train_loop:
            self.optimizer.zero_grad()
            losses = self.model(list(images), list(targets))
            total_loss = sum([losses[l] for l in losses])
            total_loss.backward()
            self.optimizer.step()

    def eval(self):
        batch_stats = []
        self.model.eval()
        with torch.no_grad():
            val_loop = tqdm(self.val_loader, desc=f"Evaluating at Epoch {self.epoch}")
            for images, targets in val_loop:
                images = list(images)
                targets = list(targets)
                outputs = self.model(images, copy.deepcopy(targets))
                batch_stats += get_batch_statistics(outputs, targets, iou_threshold=0.5)

        true_positives, pred_scores, pred_labels, labels = [np.concatenate(x, 0) for x in list(zip(*batch_stats))]
        precision, recall, AP, f1, ap_class = ap_per_class(true_positives, pred_scores, pred_labels, labels)
        print(f"mAP: {AP.mean()}")

    def visualize_example(self):
        image, label = self.dataset_train[0]
        draw_example(image.permute(1,2,0).numpy(), label, title="Training Example")
