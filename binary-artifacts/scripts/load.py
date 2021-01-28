"""
Script that downloads artifacts from the s3 store as specified in the configuration and then
exists.
"""

import logging
import os
import sys

from build_utils import (
    load_json_file,
    get_configured_s3_client,
    get_most_recent_obj,
    download_obj
)

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger('load-binaries')

BINARY_LIST_PATH = os.environ.get('BINARY_LIST_PATH', '/opt/binary_list/binary_list.json')
DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH', '/opt/download')

def download_binaries(s3_client, binary_list):
    """
    Downloads the binaries specified in the documentation from the s3 store
    """
    for binary in binary_list:
        if binary_list[binary]['version'] == 'latest':
            key = get_most_recent_obj(s3_client, binary)
            if key is None:
                LOGGER.error("Bucket %s is empty", binary)
                sys.exit(1)
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

def main():
    """
    Entrypoint function to run this file as an executable script
    """
    binary_list = load_json_file(BINARY_LIST_PATH)
    s3_client = get_configured_s3_client()
    download_binaries(s3_client, binary_list)

if __name__ == "__main__":
    main()
