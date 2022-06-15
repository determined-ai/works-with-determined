import os
import shutil

import python_pachyderm
from python_pachyderm.proto.v2.pfs.pfs_pb2 import FileType
import torch
from PIL import Image

from skimage import io
from torch.utils.data import Dataset

# ======================================================================================================================

class CatDogDataset(Dataset):
    def __init__(self, files, transform=None):
        self.files     = files
        self.transform = transform

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = self.files[idx]
        image = io.imread(img_name)
        image = Image.fromarray(image)
        if self.transform:
            image = self.transform(image)
        label = 0 if img_name.startswith('dog') else 1
        sample = (image, label)
        # print(f"Loaded image: index='{idx}', name='{img_name}'")
        return sample

# ======================================================================================================================

def download_pach_repo(pachyderm_host, pachyderm_port, repo, branch, root, token):
    print(f'Starting to download dataset: {repo}@{branch} --> {root}')

    if not os.path.exists(root):
        os.makedirs(root)

    client = python_pachyderm.Client(host=pachyderm_host, port=pachyderm_port, auth_token=token)
    files  = []

    for diff in client.diff_file((repo, branch), "/"):
        src_path = diff.new_file.file.path
        des_path = os.path.join(root, src_path[1:])
        # print(f"Got src='{src_path}', des='{des_path}'")

        if diff.new_file.file_type == FileType.FILE:
            if src_path != "":
                files.append( (src_path, des_path) )
        elif diff.new_file.file_type == FileType.DIR:
            print(f"Creating dir : {des_path}")
            os.makedirs(des_path, exist_ok=True)

    for src_path, des_path in files:
        src_file = client.get_file((repo, branch), src_path)
        # print(f'Downloading {src_path} to {des_path}')

        with open(des_path, "wb") as dest_file:
            shutil.copyfileobj(src_file, dest_file)

    print('Download operation ended')
    return files

# ========================================================================================================
