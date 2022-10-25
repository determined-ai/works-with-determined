import logging
import os
import time
from typing import Dict, List, Optional, Union

import nltk
import numpy as np
import torch
from determined.common.experimental import ModelVersion
from determined.experimental import Determined
from determined.pytorch import load_trial_from_checkpoint_path
from transformers import AutoModelForSequenceClassification

from finbert import Config, FinBert, finbert_predict
from utils import check_model

nltk.download("punkt")

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


# =============================================================================


class ModelServer(object):
    """
    Model template. You can load your model parameters in __init__ from a location accessible at runtime
    """

    def __init__(self, det_master, user, password, model_name, model_version):
        logging.info(f"Loading model version '{model_name}/{model_version}' from master at '{det_master}'")

        # Credentials to download the checkpoint from the bucket
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/service-account.json"

        if os.environ["HOME"] == "/":
            os.environ["HOME"] = "/app"

        os.environ["SERVING_MODE"] = "true"

        start = time.time()
        client = Determined(master=det_master, user=user, password=password)
        version = self.get_version(client, model_name, model_version)
        checkpoint = version.checkpoint
        checkpoint_dir = checkpoint.download()
        self.trial = load_trial_from_checkpoint_path(checkpoint_dir, map_location=torch.device("cpu"))
        self.model = self.trial.model
        end = time.time()
        delta = end - start
        logging.info(f"Checkpoint loaded in {delta} seconds")

    # -------------------------------------------------------------------------

    def get_version(self, client, model_name, model_version) -> ModelVersion:

        for version in client.get_model(model_name).get_versions():
            if version.name == model_version:
                return version

        raise AssertionError(f"Version '{model_version}' not found inside model '{model_name}'")

    # -------------------------------------------------------------------------

    def predict(
        self, X: Union[np.ndarray, List, str, bytes, Dict], names: Optional[List[str]], meta: Optional[Dict] = None
    ) -> Union[np.ndarray, List, str, bytes, Dict]:
        logging.info(f"Received request : {X}")

        input_string = X[0]

        logging.info(f"Input string : {input_string}")
        logging.info(f"Type of Input string : {type(input_string)}")

        try:
            result = finbert_predict(input_string, self.model)
            logging.info(f"Prediction type : {type(result)}")
            logging.info(f"Prediction : {result}")
            return result

        except Exception as e:
            logging.warning(f"Raised error : {e}")
            return "???"

    # =============================================================================
