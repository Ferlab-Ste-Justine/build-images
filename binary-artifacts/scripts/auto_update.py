"""
Script that will automatically continuously download artifacts from the s3 store to match the
desired configuration passed to it. will re-reload the configuration to take into account any
change there as well.
"""
import logging
import os
import signal
import sys
import time

from build_utils import (
    load_json_file,
    get_configured_s3_client,
    get_most_recent_obj,
    download_obj
)

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger('update-binaries')

BINARY_LIST_PATH = os.environ.get('BINARY_LIST_PATH', '/opt/binary_list/binary_list.json')
DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH', '/opt/download')

UPDATE_INTERVAL = int(os.environ.get('UPDATE_INTERVAL', '30'))

def update_binaries(s3_client, binary_list, latest_downloads):
    """
    Update the binaries as required given the binaries that have been downloaded so far and
    the configuration
    """
    for binary in binary_list:
        if binary_list[binary]['version'] == 'latest':
            key = get_most_recent_obj(s3_client, binary)
            if key is None:
                LOGGER.error("Bucket %s is empty", binary)
                sys.exit(1)
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
    # pylint: disable=too-few-public-methods
    """
    Handler to catch SIGINT and SIGTERM signals sent to the process and act on them
    """
    def __init__(self):
        self.terminate = False
        signal.signal(signal.SIGINT, self.signal_termination)
        signal.signal(signal.SIGTERM, self.signal_termination)

    def signal_termination(self, signum, frame):
        #pylint: disable=unused-argument
        """
        Method to flag that a signal to end the process has been received and the process should
        terminate as soon as possible
        """
        self.terminate = True

def main():
    """
    Entrypoint function to run this file as an executable script
    """
    latest_downloads = {}
    terminate_handler = TerminateHandler()
    s3_client = get_configured_s3_client()
    while not terminate_handler.terminate:
        binary_list = load_json_file(BINARY_LIST_PATH)
        update_binaries(s3_client, binary_list, latest_downloads)
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
