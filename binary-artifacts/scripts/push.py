"""
Assuming the build image produced something, this script will push the artifacts in an s3 store
"""
import logging
import os
import sys

from git import Repo
from botocore.exceptions import ClientError

from build_utils import load_json_file, get_configured_s3_client

CLONE_PATH = os.environ.get('CLONE_PATH', '/opt/repo')

BUILD_LIST_PATH = os.environ.get('BUILD_LIST_PATH', '/opt/build_list/build_list.json')

logging.basicConfig()
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOGGER = logging.getLogger('push')
LOGGER.setLevel(getattr(logging, LOG_LEVEL))

def has_built(repo_path):
    """
    Following the convention set by the plan script, determine if the build ran
    """
    return not os.path.exists(os.path.join(repo_path,'NO_BUILD'))

def push_build_artifacts(s3_client, build_list, repo_path, commit_sha):
    """
    Push the artifacts that were built in an s3 store
    """
    for bucket in build_list:
        artifact_path = build_list[bucket]
        if not os.path.isabs(artifact_path):
            artifact_path = os.path.join(repo_path, artifact_path)
        if not os.path.exists(artifact_path):
            LOGGER.error("Artifact at %s is missing and could not be uploaded", artifact_path)
            sys.exit(1)
        try:
            s3_client.upload_file(artifact_path, bucket, commit_sha)
        except ClientError as err:
            LOGGER.error("Failed to upload %s with the following error:", artifact_path)
            LOGGER.error(err)
            sys.exit(1)

def main():
    """
    Entrypoint function to run this file as an executable script
    """
    if has_built(CLONE_PATH):
        LOGGER.info("Uploading built artifacts")
        build_list = load_json_file(BUILD_LIST_PATH)
        repo = Repo(CLONE_PATH)
        sha = repo.head.commit.hexsha
        s3_client = get_configured_s3_client()
        push_build_artifacts(s3_client, build_list, CLONE_PATH, sha)
    else:
        LOGGER.info("No artifact built, skipping upload")

if __name__ == "__main__":
    main()
