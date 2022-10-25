import logging
import os
from typing import Any, Dict, List, Sequence, Tuple, Union, cast

import numpy as np
import pandas as pd
import torch
from determined import InvalidHP
from determined.pytorch import (
    DataLoader,
    LRScheduler,
    PyTorchTrial,
    PyTorchTrialContext,
)
from sklearn.metrics import f1_score
from torch.nn import CrossEntropyLoss
from transformers.optimization import AdamW, get_linear_schedule_with_warmup

import constants
import data

TorchData = Union[Dict[str, torch.Tensor], Sequence[torch.Tensor], torch.Tensor]


class FinBERTPyTorch(PyTorchTrial):
    def __init__(self, context: PyTorchTrialContext) -> None:

        self.context = context
        self.download_directory = f"/tmp/data-rank{self.context.distributed.get_rank()}"

        load_weights = os.environ.get("SERVING_MODE") != "true"
        logging.info(f"Loading weights : {load_weights}")

        if load_weights:
            files = self.download_data()
            if len(files) == 0:
                print("No data. Aborting training.")
                raise InvalidHP("No data")

            for file in files:
                if "validation.csv" in str(file):
                    self.val_csv_path = file
                if "train.csv" in str(file):
                    self.train_csv_path = file

            print(f"Found training CSV file at: {self.train_csv_path}")
            print(f"Found validation CSV file at: {self.val_csv_path}")

        self.config_class, self.tokenizer_class, self.model_class = constants.MODEL_CLASSES[
            self.context.get_hparam("model_type")
        ]

        self.label_list = ["positive", "negative", "neutral"]
        self.num_labels = len(self.label_list)

        self.loss_fct = CrossEntropyLoss()

        self.tokenizer = self.tokenizer_class.from_pretrained(
            self.context.get_data_config().get("pretrained_model_name"), do_lower_case=True, cache_dir=None
        )

        cache_dir_per_rank = f"/tmp/{self.context.distributed.get_rank()}"

        model = self.model_class.from_pretrained(
            self.context.get_data_config().get("pretrained_model_name"),
            num_labels=self.num_labels,
            cache_dir=cache_dir_per_rank,
        )

        self.model = self.context.wrap_model(model)

        no_decay = ["bias", "LayerNorm.bias", "LayerNorm.weight"]
        optimizer_grouped_parameters = [
            {
                "params": [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
                "weight_decay": self.context.get_hparam("weight_decay"),
            },
            {
                "params": [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)],
                "weight_decay": 0.0,
            },
        ]
        self.optimizer = self.context.wrap_optimizer(
            AdamW(
                optimizer_grouped_parameters,
                lr=self.context.get_hparam("learning_rate"),
                eps=self.context.get_hparam("adam_epsilon"),
            )
        )

        self.lr_scheduler = self.context.wrap_lr_scheduler(
            get_linear_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.context.get_hparam("num_warmup_steps"),
                num_training_steps=self.context.get_hparam("num_training_steps"),
            ),
            LRScheduler.StepMode.STEP_EVERY_BATCH,
        )

    def build_training_data_loader(self):
        train_dataset, _, _ = data.load_and_cache_examples(
            val_path=self.val_csv_path,
            train_path=self.train_csv_path,
            data_dir=self.download_directory,
            tokenizer=self.tokenizer,
            max_seq_length=self.context.get_hparam("max_seq_length"),
            phase="train",
        )
        return DataLoader(train_dataset, batch_size=self.context.get_per_slot_batch_size())

    def build_validation_data_loader(self):
        validation_dataset, _, _ = data.load_and_cache_examples(
            val_path=self.val_csv_path,
            train_path=self.train_csv_path,
            data_dir=self.download_directory,
            tokenizer=self.tokenizer,
            max_seq_length=self.context.get_hparam("max_seq_length"),
            phase="eval",
        )
        return DataLoader(validation_dataset, batch_size=self.context.get_per_slot_batch_size())

    def train_batch(self, batch: TorchData, epoch_idx: int, batch_idx: int):

        batch = tuple(t for t in batch)

        input_ids, attention_mask, token_type_ids, label_ids, agree_ids = batch
        logits = self.model(input_ids, attention_mask, token_type_ids)[0]

        loss = self.loss_fct(logits.view(-1, self.num_labels), label_ids.view(-1))

        self.context.backward(loss)

        self.context.step_optimizer(
            self.optimizer,
            clip_grads=lambda params: torch.nn.utils.clip_grad_norm_(params, self.context.get_hparam("max_grad_norm")),
        )
        return {"loss": loss}

    def evaluate_batch(self, batch: TorchData):

        batch = tuple(t for t in batch)

        input_ids, attention_mask, token_type_ids, label_ids, agree_ids = batch
        logits = self.model(input_ids, attention_mask, token_type_ids)[0]

        loss_fct = CrossEntropyLoss()
        valid_loss = loss_fct(logits.view(-1, self.num_labels), label_ids.view(-1))

        return {"validation_loss": valid_loss}

    def download_data(self):
        data_config = self.context.get_data_config()
        data_dir = os.path.join(self.download_directory, "data")

        files = data.download_pach_repo(
            data_config["pachyderm"]["host"],
            data_config["pachyderm"]["port"],
            data_config["pachyderm"]["repo"],
            data_config["pachyderm"]["branch"],
            data_dir,
            data_config["pachyderm"]["token"],
        )
        print(f"Data dir set to : {data_dir}")

        return [des for src, des in files]
