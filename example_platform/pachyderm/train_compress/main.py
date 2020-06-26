import os
import random
import shutil
import tarfile

def tardir(path, tar_name):
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for root, dirs, files in os.walk(path):
            for file in files:
                tar_handle.add(os.path.join(root, file))


def get_files(path):
    filelist = []
    for root, dirs, files in os.walk(path):
        for file in files:
            filelist.append((os.path.join(root, file), file))
    return filelist

os.chdir("/pfs/train")
files = get_files('./')
num_train = int(len(files)*0.8)
random.shuffle(files)
train_files = files[:num_train]
val_files = files[num_train:]
tar_name = "/pfs/out/data.tar.gz"
with tarfile.open(tar_name, "w:gz") as tf:
    for path, filename in train_files:
        tf.add(path, f'train/{filename}')
    for path, filename in val_files:
        tf.add(path, f'eval/{filename}')
tf.close()
