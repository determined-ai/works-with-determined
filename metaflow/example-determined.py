from metaflow import FlowSpec, step
import logging
import os
import re
import subprocess
from subprocess import PIPE

def script_path(filename):
    """
    A convenience function to get the absolute path to a file in this
    tutorial's directory. This allows the tutorial to be launched from any
    directory.

    """
    import os

    filepath = os.path.join(os.path.dirname(__file__))
    return os.path.join(filepath, filename)


class DeterminedFlow(FlowSpec):
    """
    A flow to train an MNIST model on Determined.

    """

    @step
    def start(self):
        """
        Placeholder step to process and transform data

        """
        self.data = "data"

        print(f"data is: {self.data}")

        # Proceed with the model training.
        self.next(self.train)

    @step
    def train(self):
        """
        This step uses the data processed in the previous step to train the model using a model definition from a Github repo.
        """

        branch = "0.13.0"
        repo_url = "https://github.com/determined-ai/determined.git"
        example_dir = "examples/official/trial/mnist_pytorch"
        detmaster = "http://latest-master.determined.ai:8080/"
        logging.basicConfig(level=logging.INFO)
        local_repo_dir = "/tmp/repo/"

        clone_command = ["git", "clone", "--single-branch", "--branch", branch, repo_url, local_repo_dir]
        clone_repo = subprocess.run(clone_command)

        # Submit determined experiment via CLI
        logging.basicConfig(level=logging.INFO)
        local_repo_dir = "/tmp/repo"

        config = os.path.join(local_repo_dir, example_dir, "const.yaml")
        context = os.path.join(local_repo_dir, example_dir)

        install_determined = ["pip", "install", "determined-cli"]
        cli = subprocess.run(install_determined)

        start_experiment = ["det", "-m", detmaster, "e", "create", config, context]
        submit = subprocess.run(start_experiment, stdout=PIPE, stderr=PIPE)
        output = str(submit.stdout)
        experiment_id = int(re.search("Created experiment (\d+)", output)[1])
        logging.info(f"Created Experiment {experiment_id}")

        # Wait for experiment to complete via CLI
        wait = subprocess.run(["det", "-m", detmaster, "e", "wait", str(experiment_id)])
        logging.info(f"Experiment {experiment_id} completed!")
        self.experiment_id = experiment_id

        self.next(self.deploy)

    @step
    def deploy(self):
        """
        Deploy the best model to an Algorithmia endpoint.

        """

        serving_endpoint = "endpoint API to be created"

        print(f"The serving endpoint can be found at {serving_endpoint}")

        self.next(self.end)

    @step
    def end(self):
        """
        Confirm completion of Flow
        """

        print("This flow is now complete.")

if __name__ == '__main__':
    DeterminedFlow()
