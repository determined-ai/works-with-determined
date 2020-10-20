import argparse
import boto3
import os


def download_s3_folder(bucket_name, s3_folder, local_dir):
    """
    Download the contents of a folder directory
    Args:
        bucket_name: the name of the s3 bucket
        s3_folder: the folder path in the s3 bucket
        local_dir: a relative or absolute directory path in the local file system
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix=s3_folder):
        target = obj.key if local_dir is None \
            else os.path.join(local_dir, os.path.basename(obj.key))
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        bucket.download_file(obj.key, target)
        print(obj.key)


def main():
    parser = argparse.ArgumentParser(description='Run Determined Example')
    parser.add_argument('bucket', type=str, help='path to context directory')
    parser.add_argument('download_folder', type=str, help='path to context directory')
    args = parser.parse_args()
    local_path = args.download_folder
    download_s3_folder(args.bucket, '', local_path)


if __name__ == '__main__':
    main()
