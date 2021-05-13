from metaflow import FlowSpec, step, Parameter
import det
import os

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

    det_master = Parameter('det-master',
                           help='Determined Master IP',
                           default="localhost:8080")

    config_file = Parameter('config-file',
                            help='Configuration file for experiment',
                            default='local.yaml')

    local_exp_dir = Parameter('local-exp-dir',
                              help='Directory with experiment code',
                              default="albert_squad_pytorch")

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

        # Override parameters if manually set by user
        det_master=self.det_master
        config_file=self.config_file
        local_exp_dir=self.local_exp_dir

        # Setup example by cloning example repo and installing the Determined CLI
        det.setup()

        # Submit determined experiment via CLI and wait for completion
        experiment_id = det.submit(det_master, config_file, local_exp_dir)

        self.experiment_id = experiment_id
        self.next(self.get_metrics)

    @step
    def get_metrics(self):
        """
        Get metric from top checkpoint

        """

        metric = det.get_metrics(self.det_master, self.experiment_id)

        print(f"TOP METRIC: {metric}")

        # Set metric to beat
        metric_to_beat = 0
        # This should always pass
        if float(metric) > metric_to_beat:
            print(f"Current metric {metric} is greater than metric to beat {metric_to_beat} - continuing pipeline")
                    
        self.next(self.end)

    @step
    def end(self):
        """
        Confirm completion of Flow
        """

        print("This flow is now complete.")

if __name__ == '__main__':
    DeterminedFlow()
