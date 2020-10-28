import copy
import os
import torch
import torchvision

from torch.utils.data import DataLoader
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from tqdm.auto import tqdm

from data import download_data, PennFudanDataset, get_transform, collate_fn, draw_example



class ObjectDetectionModel(object):

    def __init__(self, hparams):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.hparams = hparams

        self.download_directory = "/tmp/PennData/"
        self.build_model()
        self.make_data_loaders()
        self.make_optimizer()
        self.epoch = 0

    def build_model(self):
        model = fasterrcnn_resnet50_fpn(pretrained=True)
        num_classes = 2
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        self.model = model.to(self.device)

    def make_data_loaders(self):
        self._download_data()
        dataset = PennFudanDataset(os.path.join(self.download_directory, "PennFudanPed"), get_transform(), device=self.device)
        # Split 80/20 into training and validation datasets.
        train_size = int(0.8 * len(dataset))
        test_size = len(dataset) - train_size
        self.dataset_train, self.dataset_val = torch.utils.data.random_split(
            dataset, [train_size, test_size]
        )

        self.train_loader = DataLoader(self.dataset_train, batch_size=4, collate_fn=collate_fn, shuffle=True)
        self.val_loader = DataLoader(self.dataset_val, batch_size=4, collate_fn=collate_fn, shuffle=False)

    def make_optimizer(self):
        self.optimizer = torch.optim.SGD(
                self.model.parameters(),
                lr=self.hparams['lr'],
                momentum=self.hparams['m'],
                weight_decay=.0005,
            )

    def _download_data(self):
        data_url = "https://determined-ai-public-datasets.s3-us-west-2.amazonaws.com/PennFudanPed/PennFudanPed.zip"
        download_data(
            download_directory=self.download_directory,
            data_config={"url": data_url},
        )

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
        sum_iou = 0
        num_boxes = 0
        eval_loop = tqdm(self.val_loader, desc=f"Evaluating")
        self.model.eval()
        self.model.to(self.device)
        for images, targets in eval_loop:
            with torch.no_grad():
                output = self.model(list(images), copy.deepcopy(list(targets)))

            for idx, target in enumerate(targets):
                predicted_boxes = output[idx]["boxes"]
                prediction_scores = output[idx]["scores"]
                keep_indices = torchvision.ops.nms(predicted_boxes, prediction_scores, 0.1)
                predicted_boxes = torch.index_select(predicted_boxes, 0, keep_indices)
                prediction_scores = torch.index_select(prediction_scores, 0, keep_indices)

                # Tally IoU with respect to the ground truth target boxes
                target_boxes = target["boxes"]
                boxes_iou = torchvision.ops.box_iou(target_boxes, predicted_boxes)
                sum_iou += sum(max(iou_result) for iou_result in boxes_iou)
                num_boxes += len(target_boxes)
        return sum_iou / num_boxes

    def visualize_example(self):
        image, label = self.dataset_train[0]
        draw_example(image.permute(1,2,0).numpy(), label, title="Training Example")
