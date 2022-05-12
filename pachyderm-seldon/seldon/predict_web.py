from skimage import io
import matplotlib.pyplot as plt
from seldon_core.seldon_client import SeldonClient


if __name__ == '__main__':
    image = io.imread("dog.png")

    sc = SeldonClient(deployment_name="dogcat-deploy", namespace="seldon", gateway_endpoint="DEPLOY_IP:80", gateway="istio")
    out = sc.predict(transport="rest", data=image)

    if out.success:
        res = out.response['data']['ndarray'][0]
        plt.imshow(image)
        plt.title(f"Prediction: {res}")
        plt.show()
