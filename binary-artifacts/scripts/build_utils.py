"""
Module that contains common utilities used by more than one script
"""

import json
import os
import shutil

import boto3
from botocore.client import Config

def load_json_file(path):
    """
    Returns a dictionary representing the content of a json file
    """
    with open(path) as json_file:
        return json.load(json_file)

def get_s3_client(
        s3_endpoint,
        s3_region,
        s3_access_key,
        s3_secret_key
    ):
    """
    Creates a connection to an s3 store and returns it
    """
    session = boto3.session.Session()
    client = session.client(
        's3',
        region_name=s3_region,
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        config=Config(signature_version='s3v4')
    )
    return client

def get_configured_s3_client():
    """
    Function that returns a pre-configured s3 following the environment variables convention
    expected in all the scripts.
    """
    return get_s3_client(
        os.environ['S3_ENDPOINT'],
        os.environ['S3_REGION'],
        os.environ['S3_ACCESS_KEY'],
        os.environ['S3_SECRET_KEY']
    )

def get_objs_sorted_by_timestamp(s3_client, bucket):
    """
    Returns a list of object keys in a bucket, in descending order by timestamp
    """
    get_timestamp = lambda obj: obj['LastModified'].timestamp()
    response = s3_client.list_objects(
        Bucket=bucket
    )
    if 'Contents' in response:
        objs = response['Contents']
        return [obj['Key'] for obj in sorted(objs, key=get_timestamp, reverse=True)]
    return []

def get_most_recent_obj(s3_client, bucket):
    """
    Returns the key of the most recently modified object in a bucket
    """
    objs = get_objs_sorted_by_timestamp(s3_client, bucket)
    if len(objs) == 0:
        return None
    return objs[-1]

def download_obj(s3_client, bucket, obj, download_path, final_path, logger):
    # pylint: disable=too-many-arguments
    """
    Downloads a given object from the bucket. Will temporarily down it to download_path and then
    move it to final_path
    """
    logger.info("Downloading obj {obj} from bucket {bucket} at path {path}".format(
        obj=obj,
        bucket=bucket,
        path=final_path
    ))
    with open(download_path, 'wb') as downloaded_file:
        s3_client.download_fileobj(bucket, obj, downloaded_file)
        shutil.move(download_path, final_path)
