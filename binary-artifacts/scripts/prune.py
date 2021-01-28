"""
This script prunes aging artifacts so that there are no more than a given number of artifacts
per bucket.
"""
import logging
import os

from build_utils import (
    load_json_file,
    get_configured_s3_client,
    get_objs_sorted_by_timestamp
)

BUILD_LIST_PATH = os.environ.get('BUILD_LIST_PATH', '/opt/build_list/build_list.json')

MAX_ARTIFACTS_AMOUNT = int(os.environ.get('MAX_ARTIFACTS_AMOUNT', '30'))

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger('prune-binaries')

def __trim_bucket_objs(s3_client, bucket, sorted_objs, max_obj_amount):
    if len(sorted_objs) <= max_obj_amount:
        return
    objs_to_delete = sorted_objs[max_obj_amount:]
    LOGGER.info("Deleting oldest %d artifacts in bucket %s", len(objs_to_delete), bucket)
    for obj in objs_to_delete:
        s3_client.Object(bucket, obj).delete()

def trim_artifacts_listings(build_list, s3_client, max_obj_amount):
    """
    For each bucket specified in the build_list, this function will trim the oldest objects such
    that there is no more than max_obj_amount objects per bucket
    """
    for bucket in build_list:
        objs = get_objs_sorted_by_timestamp(s3_client, bucket)
        __trim_bucket_objs(s3_client, bucket, objs, max_obj_amount)

def main():
    """
    Entrypoint function to run this file as an executable script
    """
    build_list = load_json_file(BUILD_LIST_PATH)
    s3_client = get_configured_s3_client()
    trim_artifacts_listings(build_list, s3_client, MAX_ARTIFACTS_AMOUNT)

if __name__ == "__main__":
    main()
