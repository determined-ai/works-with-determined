import argparse
import json
import logging
import os

import numpy as np
import torch
from determined.experimental import Determined
from PIL import Image
from torchvision.transforms import Compose, ToTensor
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    from transformers import BertConfig, BertForQuestionAnswering, BertTokenizer


def load_data(path):
    data = {}
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            with open(os.path.join(root, name)) as f:
                context = f.readline().strip()
                questions = []
                for line in f:
                    questions.append(line.strip())
                data[name] = (context, questions)
    return data


def predict(model, question, context):
    model.eval()

    tokenizer = BertTokenizer.from_pretrained(
        "bert-base-uncased", do_lower_case=True, cache_dir=None
    )

    # ======== Tokenize ========
    # Apply the tokenizer to the input text, treating them as a text-pair.
    input_ids = tokenizer.encode(question, context)

    # Report how long the input sequence is.

    # ======== Set Segment IDs ========
    # Search the input_ids for the first instance of the `[SEP]` token.
    sep_index = input_ids.index(tokenizer.sep_token_id)

    # The number of segment A tokens includes the [SEP] token istelf.
    num_seg_a = sep_index + 1

    # The remainder are segment B.
    num_seg_b = len(input_ids) - num_seg_a

    # Construct the list of 0s and 1s.
    segment_ids = [0] * num_seg_a + [1] * num_seg_b

    # There should be a segment_id for every input token.
    assert len(segment_ids) == len(input_ids)

    # ======== Evaluate ========
    # Run our example question through the model.
    start_scores, end_scores = model(
        torch.tensor([input_ids]),
        # The tokens representing our input text.
        token_type_ids=torch.tensor([segment_ids]),
    )  # The segment IDs to differentiate question from context

    # ======== Reconstruct Answer ========
    # Find the tokens with the highest `start` and `end` scores.
    answer_start = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores)

    # Get the string versions of the input tokens.
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # Start with the first token.
    answer = tokens[answer_start]

    # Select the remaining answer tokens and join them with whitespace.
    for i in range(answer_start + 1, answer_end + 1):

        # If it's a subword token, then recombine it with the previous token.
        if tokens[i][0:2] == "##":
            answer += tokens[i][2:]

        # Otherwise, add a space then the token.
        else:
            answer += " " + tokens[i]
    return answer


def main():
    parser = argparse.ArgumentParser(description="Run Determined Example")
    parser.add_argument("data_path", type=str, help="path to context directory")
    parser.add_argument("model_name", type=str, help="path to context directory")
    parser.add_argument("det_master", type=str, help="path to context directory")
    parser.add_argument("model_version", type=int, help="path to context directory")
    args = parser.parse_args()

    print(f"Loading model {args.model_name} from master at {args.det_master}")

    checkpoint = (
        Determined(master=args.det_master)
        .get_model(args.model_name)
        .get_version(args.model_version)
    )
    # checkpoint = Determined().get_experiment(2).top_checkpoint()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    trial = checkpoint.load(map_location=device)
    model = trial.model

    data = load_data(args.data_path)
    outputs = {}
    for filename in data.keys():
        context, questions = data[filename]
        answers = []
        for question in questions:
            answer = predict(model, question, context)
            answers.append(answer)
        outputs[filename] = {"context": context, "pairs": list(zip(questions, answers))}

    with open('/tmp/outputs.txt', 'w') as f:
        f.write(json.dumps(outputs))



if __name__ == '__main__':
    main()
