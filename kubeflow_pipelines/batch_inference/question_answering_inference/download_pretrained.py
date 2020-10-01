import os
from transformers import (
    BertConfig,
    BertTokenizer,
    BertForQuestionAnswering,
)

config = BertConfig.from_pretrained(
    'bert-base-uncased',
)
model = BertForQuestionAnswering.from_pretrained(
    'bert-base-uncased',
    from_tf=False,
    config=config,
)

for i in range(8):
    cache_dir_per_rank = f"/tmp/{i}"
    os.makedirs(cache_dir_per_rank, exist_ok=True)
    model.save_pretrained(cache_dir_per_rank)

os.makedirs('/tmp/without_determined', exist_ok=True)
model.save_pretrained('/tmp/without_determined')
