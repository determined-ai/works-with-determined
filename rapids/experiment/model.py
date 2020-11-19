import numpy as np
import pandas as pd
import cudf
import cupy
import torch
import torch.nn as nn
import torch.optim as opt

from determined.pytorch import TorchData, PyTorchTrial, PyTorchTrialContext, DataLoader, LRScheduler
from pytorch_tabnet import tab_network
from pytorch_tabnet.utils import TorchDataset
from torch.utils.data import Dataset


S3_BUCKET = "determined-ai-public-datasets"
S3_KEY = "store_sales_generated"


class TorchDataset(Dataset):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __len__(self):
        return len(self.x)

    def __getitem__(self, index):
        x, y = self.x[index], self.y[index]
        return x, y

class RossmanTrial(PyTorchTrial):
    def __init__(self, context: PyTorchTrialContext):
        super().__init__(context)

        self.context = context
        clip_value = None
        if clip_value:
            self.clip_grads = lambda params: nn.utils.clip_grad_norm_(params, clip_value)
        else:
            self.clip_grads = None

        path_train = f"https://{S3_BUCKET}.s3-us-west-2.amazonaws.com/{S3_KEY}/train-xl.csv"
        path_valid = f"https://{S3_BUCKET}.s3-us-west-2.amazonaws.com/{S3_KEY}/val-xl.csv"
        path_store = f"https://{S3_BUCKET}.s3-us-west-2.amazonaws.com/{S3_KEY}/store.csv"

        # CUDF
        if self.context.get_hparam("cudf"):
            print("Reading CSVs with cudf")
            df_train = cudf.read_csv(path_train)
            df_valid = cudf.read_csv(path_valid)
            df_store = cudf.read_csv(path_store)

            print("Prepping data")
            df_train_joined = df_train.join(df_store, how='left', on='store_id', rsuffix='store').fillna(0)
            df_val_joined = df_valid.join(df_store, how='left', on='store_id', rsuffix='store').fillna(0)
            cols = df_train_joined.columns.tolist()

            X_train = df_train_joined[cols[:12] + cols[14:]].values.astype(np.float32)
            y_train = df_train_joined[cols[12]].values.astype(np.float32)
            X_valid = df_val_joined[cols[:12] + cols[14:]].values.astype(np.float32)
            y_valid = df_val_joined[cols[12]].values.astype(np.float32)
            print("Done loading data")
            self.train_dataset = TorchDataset(cupy.asnumpy(X_train), cupy.asnumpy(y_train))
            self.valid_dataset = TorchDataset(cupy.asnumpy(X_valid), cupy.asnumpy(y_valid))
        else:
            print("Reading CSVs with pandas")
            df_train = pd.read_csv(path_train)
            df_valid = pd.read_csv(path_valid)
            df_store = pd.read_csv(path_store)

            print("Prepping data")
            df_train_joined = df_train.join(df_store, how='left', on='store_id', rsuffix='store').fillna(0)
            df_val_joined = df_valid.join(df_store, how='left', on='store_id', rsuffix='store').fillna(0)
            cols = df_train_joined.columns.tolist()

            X_train = df_train_joined[cols[:12] + cols[14:]].values.astype(np.float32)
            y_train = df_train_joined[cols[12]].values.astype(np.float32)
            X_valid = df_val_joined[cols[:12] + cols[14:]].values.astype(np.float32)
            y_valid = df_val_joined[cols[12]].values.astype(np.float32)

            print("Done loading data")
            self.train_dataset = TorchDataset(X_train, y_train)
            self.valid_dataset = TorchDataset(X_valid, y_valid)

        self.lambda_sparse = 10 ** (-self.context.get_hparam("lambda_sparse"))
        self.loss_fn = nn.functional.mse_loss
        self.optimizer_params = {
            "lr": self.context.get_hparam("learning_rate"),
        }
        self.model = tab_network.TabNet(
            input_dim=22,
            output_dim=1,
            n_d=self.context.get_hparam("n_d"),
            n_a=self.context.get_hparam("n_a"),
            n_steps=self.context.get_hparam("n_steps"),
            gamma=self.context.get_hparam("gamma"),
            cat_idxs=[],
            cat_dims=[],
            cat_emb_dim=1,
            n_independent=2,
            n_shared=2,
            epsilon=1e-15,
            virtual_batch_size=256*self.context.get_hparam("virtual_batch_size"),
            momentum=self.context.get_hparam("momentum"),
            mask_type="sparsemax")
        self.model = self.context.wrap_model(self.model)
        self.optimizer = self.context.wrap_optimizer(
            opt.Adam(self.model.parameters(), **self.optimizer_params))
        lmbda = lambda epoch: self.context.get_hparam("lr_decay")
        self.lr_scheduler = self.context.wrap_lr_scheduler(
            opt.lr_scheduler.MultiplicativeLR(self.optimizer, lr_lambda=lmbda),
            step_mode=LRScheduler.StepMode.MANUAL_STEP
        )


    def update_and_step_lr(self, batch_idx: int):
        # TabNet paper decayed 0.95 about 10 times throughout training.
        if (batch_idx + 1) % 2000 == 0:
            print("Stepping LR scheduler")
            self.lr_scheduler.step()


    def train_batch(self, batch: TorchData, epoch_idx: int, batch_idx: int):
        self.model.train()
        data, targets = batch

        output, M_loss = self.model(data)
        output = torch.flatten(output)

        loss = self.loss_fn(output, targets)
        loss -= self.lambda_sparse * M_loss

        self.context.backward(loss)
        self.context.step_optimizer(self.optimizer,
                                    clip_grads=self.clip_grads,
                                    auto_zero_grads=True)
        self.update_and_step_lr(batch_idx)
        return {"loss": loss.item()}


    def evaluate_batch(self, batch: TorchData):
        data, targets = batch

        self.model.eval()
        output, M_loss = self.model(data)
        output = torch.flatten(output)

        loss = self.loss_fn(output, targets)
        loss -= self.lambda_sparse * M_loss

        return {"validation_loss": loss.item()}


    def build_training_data_loader(self):
        return DataLoader(self.train_dataset,
                          batch_size=self.context.get_per_slot_batch_size(),
                          drop_last=True)


    def build_validation_data_loader(self):
        return DataLoader(self.valid_dataset,
                          batch_size=self.context.get_per_slot_batch_size(),
                          drop_last=True)
