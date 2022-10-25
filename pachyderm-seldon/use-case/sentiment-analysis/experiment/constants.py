from transformers import (
    BertConfig,
    BertTokenizer, 
    BertForSequenceClassification,
)

MODEL_CLASSES = {
    "bert_for_classification": (BertConfig, 
    BertTokenizer, 
    BertForSequenceClassification),
}