# This script is used to create three files: train.csv, validation.csv, test.csv

'''
For the sentiment analysis, we used Financial PhraseBank from Malo et al. (2014). The dataset can be downloaded from this link. If you want to train the model on the same dataset, after downloading it, you should create three files under the data/sentiment_data folder as train.csv, validation.csv, test.csv. To create these files, do the following steps:
Link: https://www.researchgate.net/publication/251231364_FinancialPhraseBank-v10
1. Download the Financial PhraseBank from the above link.
2. Get the path of Sentences_50Agree.txt file in the FinancialPhraseBank-v1.0 zip.
3. Run the datasets script: python scripts/datasets.py --data_path <path to Sentences_50Agree.txt>
'''

import argparse
import pandas as pd
from sklearn.model_selection import train_test_split
import os

if not os.path.exists('data/sentiment_data'):
    os.makedirs('data/sentiment_data')

parser = argparse.ArgumentParser(description='Sentiment analyzer')
parser.add_argument('--data_path', type=str, help='Path to the text file.')

args = parser.parse_args()
data = pd.read_csv(args.data_path, sep='.@', names=['text','label'], encoding="ISO-8859-1")

train, test = train_test_split(data, test_size=0.2, random_state=0)
train, valid = train_test_split(train, test_size=0.1, random_state=0)

train.to_csv('data/sentiment_data/train.csv',sep='\t')
test.to_csv('data/sentiment_data/test.csv',sep='\t')
valid.to_csv('data/sentiment_data/validation.csv',sep='\t')