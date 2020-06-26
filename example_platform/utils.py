import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from PIL import Image
from det.data import get_test_transforms
import torch

def predict(model, image):
    labels = ['dog', 'cat']
    transform = get_test_transforms()
    image = io.imread(image)
    test_image = Image.fromarray(image)
    test_image = transform(test_image)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    with torch.no_grad():
        pred = np.argmax(model(test_image.unsqueeze(0).to(device))[0].cpu().numpy())
    plt.imshow(image)
    plt.title(f"Prediction: {labels[pred]}")
    plt.show()
