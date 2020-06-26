import argparse
import requests
import json
import numpy as np


def main():
    parser = argparse.ArgumentParser(description='Run Determined Example')
    parser.add_argument('endpoint', type=str, help='deployment name')
    args = parser.parse_args()
    image = np.random.randint(0,255, size=(28,28))
    data = {'data': {'ndarray': image.tolist()}}
    headers = {'content-type': 'application/json'}

    prediction = requests.post(url=args.endpoint, data=json.dumps(data), headers=headers, verify = False).json()
    print(prediction['jsonData'])


if __name__ == '__main__':
    main()
