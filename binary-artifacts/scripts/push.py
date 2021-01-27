import logging
import os

from git import Repo

from build_utils import load_json_file, get_s3_client

CLONE_PATH = os.environ.get('CLONE_PATH', '/opt/repo')

BUILD_LIST_PATH = os.environ.get('BUILD_LIST_PATH', '/opt/build_list/build_list.json')

S3_ENDPOINT = os.environ['S3_ENDPOINT']
S3_REGION = os.environ['S3_REGION']
S3_ACCESS_KEY = os.environ['S3_ACCESS_KEY']
S3_SECRET_KEY = os.environ['S3_SECRET_KEY']

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
LOGGER = logging.getLogger('push-binaries')

def has_built(repo_path):
    return not os.path.exists(os.path.join(repo_path,'NO_BUILD'))

def push_build_artifacts(s3_client, build_list, repo_path, commit_sha):
    for bucket in build_list:
        artifact_path = build_list[bucket]
        if not os.path.isabs(artifact_path):
            artifact_path = os.path.join(repo_path, artifact_path)
        if not os.path.exists(artifact_path):
            LOGGER.error("Artifact at {artifact_path} is missing and could not be uploaded".format(artifact_path=artifact_path))
            exit(1)
        try:
            s3_client.upload_file(artifact_path, bucket, commit_sha)
        except ClientError as err:
            LOGGER.error("Failed to upload {artifact_path} with the following error:".format(artifact_path=artifact_path))
            LOGGER.error(err)
            exit(1)

if __name__ == "__main__":
    if has_built(CLONE_PATH):
        LOGGER.info("Uploading built artifacts")
        build_list = load_json_file(BUILD_LIST_PATH)
        repo = Repo(CLONE_PATH)
        sha = repo.head.commit.hexsha
        s3_client = get_s3_client(
            S3_ENDPOINT,
            S3_REGION,
            S3_ACCESS_KEY,
            S3_SECRET_KEY
        )
        push_build_artifacts(s3_client, build_list, CLONE_PATH, sha)
    else:
        LOGGER.info("No artifact built, skipping upload")