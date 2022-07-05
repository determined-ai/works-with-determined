import os
import torch
from torch.utils.data import TensorDataset
from utils import convert_examples_to_features, FinSentProcessor
import pandas as pd

def load_and_cache_examples(data_dir: str, tokenizer, max_seq_length, phase):
    # Processor
    processors = {"finsent": FinSentProcessor}
    processor = processors["finsent"]()

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if phase == "eval":
        eval_url = "./data/sentiment_data/validation.csv"
        eval_file = "eval.csv"
        df = pd.read_csv(eval_url, on_bad_lines='skip', sep='\t', lineterminator='\n')
        df = df.drop('Unnamed: 0', 1)
        df.to_csv(data_dir + "/" + eval_file, sep='\t')
    else:
        train_url = "./data/sentiment_data/train.csv"
        train_file = "train.csv"
        df = pd.read_csv(train_url, on_bad_lines='skip', sep='\t', lineterminator='\n') 
        df = df.drop('Unnamed: 0', 1)
        df.to_csv(data_dir + "/" + train_file, sep='\t')
    
    # Get examples
    examples = processor.get_examples(data_dir, phase)

    # Examples to features
    label_list = ['positive', 'negative', 'neutral']
    output_mode = "classification"
    features = convert_examples_to_features(examples, label_list,
                                                max_seq_length,
                                                tokenizer,
                                                output_mode)

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
    '''
    Return class weights tensor
    '''
    train = pd.read_csv(
        os.path.join(data_dir, "train.csv"),
        sep="\t",
        index_col=False,
    )
    weights = list()
    label_list = ['positive', 'negative', 'neutral']
    labels = label_list

    class_weights = [
        train.shape[0] / train[train.label == label].shape[0]
        for label in labels
    ]

    return torch.tensor(class_weights)