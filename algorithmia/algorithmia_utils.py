import Algorithmia
import urllib.parse
from git import Git, Repo, remote
from retry import retry


class Progress(remote.RemoteProgress):
    def line_dropped(self, line):
        print(line)

    def update(self, *args):
        print(self._cur_line)


class AlgorithmiaUtils:
    def __init__(self, api_key, username, algo_name, local_dir):
        self.api_key = api_key
        self.username = username
        self.algo_name = algo_name
        self.local_dir = local_dir

        self.algo_namespace = f"{self.username}/{self.algo_name}"
        self.algo_script_path = "{}/{}/src/{}.py".format(
            self.local_dir, algo_name, algo_name
        )
        self.dependency_file_path = "{}/{}/{}".format(
            self.local_dir, algo_name, "requirements.txt"
        )

        self.algo_client = Algorithmia.client(self.api_key)

    def create_algorithm(self):
        details = {
            "summary": "ALGO_SUMMARY",
            "label": "ALGO_LABEL",
            "tagline": "ALGO_TAGLINE",
        }
        settings = {
            "source_visibility": "closed",
            "package_set": "python37",
            "license": "apl",
            "network_access": "full",
            "pipeline_enabled": True,
        }
        self.algo_client.algo(self.algo_namespace).create(details, settings)

    def clone_algorithm_repo(self):
        # Encoding the API key, so we can use it in the git URL
        encoded_api_key = urllib.parse.quote_plus(self.api_key)

        algo_repo = "https://{}:{}@git.algorithmia.com/git/{}/{}.git".format(
            self.username, encoded_api_key, self.username, self.algo_name
        )
        p = Progress()
        self.repo = Repo.clone_from(
            algo_repo, "{}/{}".format(self.local_dir, self.algo_name), progress=p
        )

    def push_algo_script_with_dependencies(self, filenames):
        if not self.repo:
            self.repo = Repo("{}/{}".format(local_dir, algo_name))
        
        files = []
        for filename in filenames:
            files.append(f"src/{filename}")            
        files.append("requirements.txt")
        
        self.repo.index.add(files)
        self.repo.index.commit("Updated algorithm files")
        p = Progress()
        self.repo.remote(name="origin").push(progress=p)

    def upload_model_to_algorithmia(
        self, local_path, algorithmia_data_path, model_name
    ):
        if not self.algo_client.dir(algorithmia_data_path).exists():
            self.algo_client.dir(algorithmia_data_path).create()
        algorithmia_path = "{}/{}".format(algorithmia_data_path, model_name)
        result = self.algo_client.file(algorithmia_path).putFile(local_path)
        # TODO: Act on the result object, have a return value

    # Call algorithm until the algo hash endpoint becomes available, up to 10 seconds
    @retry(Algorithmia.errors.AlgorithmException, tries=10, delay=1)
    def call_latest_algo_version(self, input):
        latest_algo_hash = (
            self.algo_client.algo(self.algo_namespace).info().version_info.git_hash
        )
        algo = self.algo_client.algo(
            "{}/{}".format(self.algo_namespace, latest_algo_hash)
        )
        algo.set_options(timeout=300, stdout=False)
        algo_pipe_result = algo.pipe(input)
        return algo_pipe_result
