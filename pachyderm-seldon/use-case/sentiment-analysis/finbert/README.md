# FinBERT Porting Model Demo
This model porting demo was developed in May 2022. 

The original finBERT model, that was ported to the Determined API, can be found here.
https://github.com/ProsusAI/finBERT

FinBERT is a pre-trained NLP model to analyze sentiment of financial text. It is built by further training the BERT language model in the finance domain, using a large financial corpus and thereby fine-tuning it for financial sentiment classification. For the details, please see FinBERT publication: 
Financial Sentiment Analysis with Pre-trained Language Models.
https://arxiv.org/pdf/1908.10063.pdf

## Set Up

### Cluster Setup
Refer to the following documentations for setting up a Determined cluster on cloud.
Note that a Determined cluster can be installed on Amazon Web Services (AWS), Google Cloud Platform (GCP), an on-premise cluster, or on a local development machine.

Install Determined on AWS
https://docs.determined.ai/latest/sysadmin-deploy-on-aws/install-on-aws.html#install-aws

```sh
det deploy aws up --cluster-id CLUSTER_ID --keypair KEYPAIR_NAME
```

Install Determined on GCP
https://docs.determined.ai/latest/sysadmin-deploy-on-gcp/install-gcp.html#install-gcp

```sh
det deploy gcp up --cluster-id CLUSTER_ID --project-id PROJECT_ID
```
### Datasets
We use the Financial PhraseBank from Malo et al. (2014). The dataset can be downloaded from this link.

https://www.researchgate.net/publication/251231364_FinancialPhraseBank-v10

After downloading it, you should create three files under the data/sentiment_data folder as train.csv, validation.csv, test.csv. To create these files, do the following steps:

- Download the Financial PhraseBank from the above link.
- Get the path of Sentences_50Agree.txt file in the FinancialPhraseBank-v1.0 zip.
- Run the datasets script: 

```sh
python datasets.py --data_path <path to Sentences_50Agree.txt>
```
### Run Experiments on a Determined Cluster

```sh
cd finbert/experiments
```
Run a constant-parameter experiment:

```sh
det -m <MASTER_URL> e create const.yaml .
```
Run a distributed training experiment:

```sh
det -m <MASTER_URL> e create distributed.yaml .
```
The validation loss should reach about 0.365 after one epoch.