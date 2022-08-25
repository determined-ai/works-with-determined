from typing import Any, Dict, Union, Sequence
from sklearn.metrics import f1_score
import torch
from torch.nn import CrossEntropyLoss
from determined.pytorch import DataLoader, PyTorchTrial, PyTorchTrialContext, LRScheduler
import data
import constants
import numpy as np
import pandas as pd

from transformers.optimization import AdamW, get_linear_schedule_with_warmup

TorchData = Union[Dict[str, torch.Tensor], Sequence[torch.Tensor], torch.Tensor]

class FinBERTPyTorch(PyTorchTrial):
    def __init__(self, context: PyTorchTrialContext) -> None:

        self.context = context

        self.download_directory = f"/tmp/data-rank{self.context.distributed.get_rank()}"

        self.config_class, self.tokenizer_class, self.model_class = constants.MODEL_CLASSES[
            self.context.get_hparam("model_type")
        ]

        self.label_list = ['positive', 'negative', 'neutral']
        self.num_labels = len(self.label_list)

        self.loss_fct = CrossEntropyLoss()

        self.tokenizer = self.tokenizer_class.from_pretrained(
            self.context.get_data_config().get("pretrained_model_name"),
            do_lower_case=True,
            cache_dir=None
        )
        
        cache_dir_per_rank = f"/tmp/{self.context.distributed.get_rank()}"

        model = self.model_class.from_pretrained(
                self.context.get_data_config().get("pretrained_model_name"),
                num_labels = self.num_labels,
                cache_dir = cache_dir_per_rank)
  
        self.model = self.context.wrap_model(model)   

        no_decay = ["bias", "LayerNorm.bias", "LayerNorm.weight"]
        optimizer_grouped_parameters = [
            {'params': [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
                'weight_decay': self.context.get_hparam("weight_decay")},
            {'params': [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
        ]
        self.optimizer = self.context.wrap_optimizer(AdamW(
            optimizer_grouped_parameters,
            lr=self.context.get_hparam("learning_rate"),
            eps=self.context.get_hparam("adam_epsilon")
        ))

        self.lr_scheduler = self.context.wrap_lr_scheduler(
            get_linear_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=self.context.get_hparam("num_warmup_steps"),
                num_training_steps=self.context.get_hparam("num_training_steps"),
            ),
            LRScheduler.StepMode.STEP_EVERY_BATCH
        )

    def build_training_data_loader(self):
        train_dataset, _, _  = data.load_and_cache_examples(
            data_dir=self.download_directory,
            tokenizer=self.tokenizer,
            max_seq_length=self.context.get_hparam("max_seq_length"),
            phase="train",
        )
        return DataLoader(train_dataset, batch_size=self.context.get_per_slot_batch_size())

    def build_validation_data_loader(self):
        validation_dataset, _, _ = data.load_and_cache_examples(
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
            clip_grads=lambda params: torch.nn.utils.clip_grad_norm_(
                params, self.context.get_hparam("max_grad_norm")
            )
        )
        return {"loss": loss}

    def evaluate_batch(self, batch: TorchData):

        batch = tuple(t for t in batch)

        input_ids, attention_mask, token_type_ids, label_ids, agree_ids = batch
        logits = self.model(input_ids, attention_mask, token_type_ids)[0]

        loss_fct = CrossEntropyLoss()
        valid_loss = loss_fct(logits.view(-1, self.num_labels), label_ids.view(-1))

        return {"validation_loss": valid_loss}
    
    