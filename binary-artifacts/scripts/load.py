import logging
import os
import shutil

from build_utils import (
    load_json_file,
    get_s3_client,
    get_most_recent_obj,
    download_obj
)

S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_REGION = os.environ.get('S3_REGION')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger('load-binaries')

BINARY_LIST_PATH = os.environ.get('BINARY_LIST_PATH', '/opt/binary_list/binary_list.json')
DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH', '/opt/download')

def download_binaries(s3_client, binary_list):
    for binary in binary_list:
        if binary_list[binary]['version'] == 'latest':
            key = get_most_recent_obj(s3_client, binary)
            if key is None:
                LOGGER.error("Bucket {bucket} is empty".format(bucket=binary))
                exit(1)
        else:
            key = binary
        download_path = os.path.join(DOWNLOAD_PATH, key)
        download_obj(
            s3_client,
            binary,
            key,
            download_path,
            binary_list[binary]['path'],
            LOGGER
        )

if __name__ == "__main__":
    binary_list = load_json_file(BINARY_LIST_PATH)
    s3_client = get_s3_client(
        S3_ENDPOINT,
        S3_REGION,
        S3_ACCESS_KEY,
        S3_SECRET_KEY
    )
    download_binaries(s3_client, binary_list) 