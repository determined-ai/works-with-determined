from metaflow import FlowSpec, step
import logging
import det

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
        self.data = "example data"

        print(f"This is your data: {self.data}")

        # Proceed with the model training.
        self.next(self.train)

    @step
    def train(self):
        """
        This step uses the data processed in the previous step to train the model using a model definition from a Github repo.
        """

        # User inputs
        # Indicate the Determined version you're running and your Determined Master's IP
        det_version = "0.13.0"
        det_master = "http://localhost:8080"
        local_repo_dir = "/tmp/repo/"

        # Default inputs
        repo_url = "https://github.com/determined-ai/determined.git"
        example_dir = "examples/official/trial/mnist_pytorch"
        config_file = "const.yaml"

        # Setup example by cloning example repo and installing the Determined CLI
        config, context = det.setup(det_version, repo_url, example_dir, config_file, local_repo_dir)

        # Submit determined experiment via CLI and wait for completion
        experiment_id = det.submit(det_master, config, context)

        self.experiment_id = experiment_id
        self.next(self.deploy)

    @step
    def deploy(self):
        """
        Deploy the best model to an endpoint.

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
