import os
import time
from typing import Iterable, Dict, Union, List

from determined.experimental import Determined
from determined.pytorch import load_trial_from_checkpoint_path
from PIL import Image
import numpy as np
import logging
import torch

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# =============================================================================

class ImageClassificationModel(object):
    """
    Model template. You can load your model parameters in __init__ from a location accessible at runtime
    """

    def __init__(self, det_master=None, model_name=None, user=None, password=None):
        logging.info(f"Loading model with name '{model_name}' from master at '{det_master}'")

        # Credentials to download the checkpoint from the bucket
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service-account.json'

        if os.environ['HOME'] == '/':
            os.environ['HOME'] = '/app'

        os.environ['SERVING_MODE'] = 'true'

        start = time.time()
        client = Determined(master=det_master, user=user, password=password)
        version = client.get_model(model_name).get_version()
        checkpoint = version.checkpoint
        checkpoint_dir = checkpoint.download()
        self.model = load_trial_from_checkpoint_path(checkpoint_dir, map_location=torch.device('cpu'))
        end = time.time()
        delta = end - start
        logging.info(f'Checkpoint loaded in {delta} seconds')

    # -------------------------------------------------------------------------

    def predict(self, X: np.ndarray, names: Iterable[str] = None, meta: Dict = None) -> Union[np.ndarray, List, str, bytes]:
        logging.info(f"Received request : \n{X}")

        image = Image.fromarray(X.astype(np.uint8))
        logging.info(f"Image size : {image.size}")

        try:
            prediction = self.model.predict(image)
            logging.info(f"Prediction : {prediction}")

            return prediction
        except Exception as e:
            logging.warning(f"Raised error : {e}")
            return "???"

# =============================================================================
