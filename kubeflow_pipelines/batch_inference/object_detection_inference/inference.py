from determined.experimental import Determined
from torchvision.transforms import Compose, ToTensor
import argparse
from PIL import Image
import numpy as np
import torch
import logging
import os
import json

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def get_transform():
    transforms = []
    transforms.append(ToTensor())
    return Compose(transforms)


def main():
    parser = argparse.ArgumentParser(description='Run Determined Example')
    parser.add_argument('data_path', type=str, help='path to context directory')
    parser.add_argument('model_name', type=str, help='path to context directory')
    parser.add_argument('det_master', type=str, help='path to context directory')
    parser.add_argument('model_version', type=str, help='path to context directory')
    args = parser.parse_args()

    logging.info(f"Loading model {args.model_name} from master at {args.det_master}")

    checkpoint = Determined(master=args.det_master).get_model(args.model_name).get_version(args.model_version)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    trial = checkpoint.load(map_location=device)
    model = trial.model
    model.eval()
    logging.info("Loaded checkpoint")
    transform = get_transform()

    image_paths = []
    for (root, dirs, files) in os.walk(args.data_path):
        for file in files:
            if file.endswith('.jpg'):
                image_paths.append(os.path.join(root, file))

    outputs = []
    for path in image_paths:
        image = Image.open(path)
        with torch.no_grad():
            image = transform(image)
            pred = model(image.unsqueeze(0).to(device))[0]
        boxes = pred['boxes'].cpu().numpy().tolist()
        labels = pred['labels'].cpu().numpy().tolist()
        scores = pred['scores'].cpu().numpy().tolist()
        out_json = {'boxes': boxes, 'scores': scores, 'labels': labels, 'filename': path}
        outputs.append(json.dumps(out_json))
    with open('/tmp/outputs.txt', 'w') as f:
        for output in outputs:
            f.write(output + '\n')
    f.close()
    logging.info(outputs)


if __name__ == '__main__':
    main()
