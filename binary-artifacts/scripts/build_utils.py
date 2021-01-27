import json
import boto3
from botocore.client import Config

def load_json_file(path):
    with open(path) as f:
        return json.load(f)

def get_s3_client(
        s3_endpoint, 
        s3_region, 
        s3_access_key, 
        s3_secret_key
    ):
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

def get_objs_sorted_by_timestamp(s3_client, bucket):
    get_timestamp = lambda obj: obj['LastModified'].timestamp()
    response = s3_client.list_objects(
        Bucket=bucket
    )
    if 'Contents' in response:
        objs = response['Contents']
        return [obj['Key'] for obj in sorted(objs, key=get_timestamp, reverse=True)]
    else:
        return []

def get_most_recent_obj(s3_client, bucket):
    objs = get_objs_sorted_by_timestamp(s3_client, bucket)
    if len(objs) == 0:
        return None
    return objs[-1]

def download_obj(s3_client, bucket, obj, download_path, final_path, logger):
        logger.info("Downloading obj {obj} from bucket {bucket} at path {path}".format(
            obj=obj,
            bucket=bucket,
            path=final_path
        ))
        with open(download_path, 'wb') as f:
            s3_client.download_fileobj(bucket, obj, f)
            shutil.move(download_path, final_path)