import sys
from skimage import io
from ModelServer import ModelServer


if __name__ == '__main__':
    det_master    = sys.argv[1]
    model_name    = sys.argv[2]
    model_version = sys.argv[3]

    print(f"Loading model from '{det_master}'")
    model = ModelServer(det_master, 'determined', 'dai', model_name, model_version)
    print('Model loaded.')
    image = io.imread('dog.png')
    outcome = model.predict(image, None, None)
    print(f'Prediction: {outcome}')
