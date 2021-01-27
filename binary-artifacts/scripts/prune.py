import logging
import os

from build_utils import (
    load_json_file,
    get_s3_client,
    get_objs_sorted_by_timestamp
)

BUILD_LIST_PATH = os.environ.get('BUILD_LIST_PATH', '/opt/build_list/build_list.json')

S3_ENDPOINT = os.environ['S3_ENDPOINT']
S3_REGION = os.environ['S3_REGION']
S3_ACCESS_KEY = os.environ['S3_ACCESS_KEY']
S3_SECRET_KEY = os.environ['S3_SECRET_KEY']

MAX_ARTIFACTS_AMOUNT = int(os.environ.get('MAX_ARTIFACTS_AMOUNT', '30'))

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger('prune-binaries')

def __trim_bucket_objs(s3_client, bucket, sorted_objs, max_obj_amount):
    if len(sorted_objs) <= max_obj_amount:
        return
    objs_to_delete = sorted_objs[max_obj_amount:]
    LOGGER.info("Deleting oldest {count} artifacts in bucket {bucket}".format(count=len(objs_to_delete), bucket=bucket))
    for obj in objs_to_delete:
        s3_client.Object(bucket, obj).delete()

def trim_artifacts_listings(build_list, s3_client, max_obj_amount):
    for bucket in build_list:
        objs = get_objs_sorted_by_timestamp(s3_client, bucket)

if __name__ == "__main__":
    build_list = load_json_file(BUILD_LIST_PATH)
    s3_client = get_s3_client(
        S3_ENDPOINT,
        S3_REGION,
        S3_ACCESS_KEY,
        S3_SECRET_KEY
    )
    trim_artifacts_listings(build_list, s3_client, MAX_ARTIFACTS_AMOUNT)
