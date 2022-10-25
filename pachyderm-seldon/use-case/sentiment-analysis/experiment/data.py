import os
import shutil

import pandas as pd
import python_pachyderm
import torch
from python_pachyderm.proto.v2.pfs.pfs_pb2 import FileType
from torch.utils.data import TensorDataset

from utils import FinSentProcessor, convert_examples_to_features


def load_and_cache_examples(val_path: str, train_path: str, data_dir: str, tokenizer, max_seq_length, phase):
    # Processor
    processors = {"finsent": FinSentProcessor}
    processor = processors["finsent"]()

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if phase == "eval":
        # eval_url = data_dir + "/data/data/sentiment_data/validation.csv"
        eval_file = "eval.csv"
        df = pd.read_csv(val_path, on_bad_lines="skip", sep="\t", lineterminator="\n")
        df = df.drop("Unnamed: 0", 1)
        df.to_csv(data_dir + "/" + eval_file, sep="\t")
    else:
        # train_url = data_dir + "/data/data/sentiment_data/train.csv"
        train_file = "train.csv"
        df = pd.read_csv(train_path, on_bad_lines="skip", sep="\t", lineterminator="\n")
        df = df.drop("Unnamed: 0", 1)
        df.to_csv(data_dir + "/" + train_file, sep="\t")

    # Get examples
    examples = processor.get_examples(data_dir, phase)

    # Examples to features
    label_list = ["positive", "negative", "neutral"]
    output_mode = "classification"
    features = convert_examples_to_features(examples, label_list, max_seq_length, tokenizer, output_mode)

    # Load the data, make it into TensorDataset
    all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
    all_attention_mask = torch.tensor([f.attention_mask for f in features], dtype=torch.long)
    all_token_type_ids = torch.tensor([f.token_type_ids for f in features], dtype=torch.long)
    all_label_ids = torch.tensor([f.label_id for f in features], dtype=torch.long)
    try:
        all_agree_ids = torch.tensor([f.agree for f in features], dtype=torch.long)
    except:
        all_agree_ids = torch.tensor([0.0 for f in features], dtype=torch.long)

    dataset = TensorDataset(all_input_ids, all_attention_mask, all_token_type_ids, all_label_ids, all_agree_ids)

    return dataset, examples, features


def get_weights(data_dir: str):
    """
    Return class weights tensor
    """
    train = pd.read_csv(
        os.path.join(data_dir, "train.csv"),
        sep="\t",
        index_col=False,
    )
    weights = list()
    label_list = ["positive", "negative", "neutral"]
    labels = label_list

    class_weights = [train.shape[0] / train[train.label == label].shape[0] for label in labels]

    return torch.tensor(class_weights)


# ======================================================================================================================


def download_pach_repo(pachyderm_host, pachyderm_port, repo, branch, root, token):
    print(f"Starting to download dataset: {repo}@{branch} --> {root}")

    if not os.path.exists(root):
        os.makedirs(root)

    client = python_pachyderm.Client(host=pachyderm_host, port=pachyderm_port, auth_token=token)
    files = []

    for diff in client.diff_file((repo, branch), "/"):
        src_path = diff.new_file.file.path
        des_path = os.path.join(root, src_path[1:])
        # print(f"Got src='{src_path}', des='{des_path}'")

        if diff.new_file.file_type == FileType.FILE:
            if src_path != "":
                files.append((src_path, des_path))
        elif diff.new_file.file_type == FileType.DIR:
            print(f"Creating dir : {des_path}")
            os.makedirs(des_path, exist_ok=True)

    for src_path, des_path in files:
        src_file = client.get_file((repo, branch), src_path)
        # print(f'Downloading {src_path} to {des_path}')

        with open(des_path, "wb") as dest_file:
            shutil.copyfileobj(src_file, dest_file)

    print("Download operation ended")
    return files


# ========================================================================================================
