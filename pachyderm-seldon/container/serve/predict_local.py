from skimage import io
from ModelServer import ModelServer


if __name__ == '__main__':
    model = ModelServer(det_master='HOSTNAME_OR_URL', model_name='dogs-and-cats', user='determined', password='PASSWORD')
    print('Model loaded.')
    image = io.imread('dog.png')
    outcome = model.predict(image, None, None)
    print(f'Prediction: {outcome}')
