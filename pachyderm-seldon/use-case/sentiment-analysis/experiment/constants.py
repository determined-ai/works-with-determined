from transformers import (
    BertConfig,
    BertTokenizer, 
    BertForSequenceClassification,
)

MODEL_CLASSES = {
    "bert": (BertConfig, 
    BertTokenizer, 
    BertForSequenceClassification),
}