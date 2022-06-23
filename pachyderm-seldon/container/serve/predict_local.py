import os
from skimage import io
from ModelServer import ModelServer


if __name__ == '__main__':
    model = ModelServer(det_master='DETERMINED_HOST', model_name='dogcat-model', user='determined', password='dai')
    print('Model loaded.')

    image = io.imread('dog.png')

    outcome = model.predict(image)
    print(f'Prediction: {outcome}')
