import logging
import os
import signal
import shutil
import time

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
LOGGER = logging.getLogger('update-binaries')

BINARY_LIST_PATH = os.environ.get('BINARY_LIST_PATH', '/opt/binary_list/binary_list.json')
DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH', '/opt/download')

UPDATE_INTERVAL = int(os.environ.get('UPDATE_INTERVAL', '30'))

def update_binaries(s3_client, binary_list, latest_downloads):
    for binary in binary_list:
        if binary_list[binary]['version'] == 'latest':
            key = get_most_recent_obj(s3_client, binary)
            if key is None:
                LOGGER.error("Bucket {bucket} is empty".format(bucket=binary))
                exit(1)
        else:
            key = binary
        if binary not in latest_downloads or latest_downloads[binary] != key:
            latest_downloads[binary] = key
            download_path = os.path.join(DOWNLOAD_PATH, key)
            download_obj(
                s3_client,
                binary,
                key,
                download_path,
                binary_list[binary]['path'],
                LOGGER
            )

class TerminateHandler:
  def __init__(self):
    self.terminate = False
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def signal_termination(self, signum, frame):
    self.terminate = True

if __name__ == "__main__":
    latest_downloads = {}
    terminate_handler = TerminateHandler()
    s3_client = get_s3_client(
        S3_ENDPOINT,
        S3_REGION,
        S3_ACCESS_KEY,
        S3_SECRET_KEY
    )
    while not terminate_handler.terminate:
        binary_list = load_json_file(BINARY_LIST_PATH)
        download_binaries(s3_client, binary_list, latest_downloads)
        time.sleep(UPDATE_INTERVAL) 