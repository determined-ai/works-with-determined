import os
from skimage import io
from ImageClassificationModel import ImageClassificationModel


if __name__ == '__main__':
    model = ImageClassificationModel(det_master='DETERMINED_HOST', model_name='dogcat-model', user='determined', password='xxx')
    print('Model loaded.')

    image = io.imread('dog.png')

    outcome = model.predict(image)
    print(f'Prediction: {outcome}')
