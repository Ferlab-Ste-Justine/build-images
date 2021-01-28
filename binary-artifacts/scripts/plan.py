"""
Script that checks an s3 store for existing binaries and generates a build script that either
runs the build if some binaries are missing or does nothing is all binaries are there.
"""

import os

from jinja2 import Template
from git import Repo

from build_utils import load_json_file, get_configured_s3_client

GIT_REPO = os.environ['GIT_REPO']
GIT_BRANCH = os.environ.get('GIT_BRANCH', 'main')
CLONE_PATH = os.environ.get('CLONE_PATH', '/opt/repo')

BUILD_LIST_PATH = os.environ.get('BUILD_LIST_PATH', '/opt/build_list/build_list.json')

def setup_repo(repo_url, branch, path):
    """
    Clone the given repo and change it to the desired branch
    """
    repo = Repo.clone_from(repo_url, path)
    repo.git.checkout(branch)
    return repo

def is_build_required(s3_client, build_list, commit_sha):
    """
    Determine whether a build will be required given the artifacts in s3 store and the build list
    """
    for bucket in build_list:
        key = commit_sha
        response = s3_client.list_objects(
            Bucket=bucket,
            Prefix=key
        )
        if 'Contents' in response:
            artifacts = [obj['Key'] for obj in response['Contents']]
        else:
            artifacts = []
        if not key in artifacts:
            return True
    return False

def render_build_script(repo_path, build_required, commit_sha):
    """
    Render the build script that will run in the image which runs the build
    """
    with open('/opt/scripts/RUN_BUILD.sh.j2') as build_template:
        tmpl = Template(build_template.read())
        build_file_path = os.path.join(repo_path, "RUN_BUILD.sh")
        with open(build_file_path, "w+") as build_script:
            build_script.write(tmpl.render(
                run_build = build_required,
                sha = commit_sha,
                clone_path = repo_path
            ))
        os.chmod(build_file_path, 555)

def main():
    """
    Entrypoint function to run this file as an executable script
    """
    repo = setup_repo(GIT_REPO, GIT_BRANCH, CLONE_PATH)
    sha = repo.head.commit.hexsha
    build_list = load_json_file(BUILD_LIST_PATH)
    s3_client = get_configured_s3_client()
    build_required = is_build_required(s3_client, build_list, sha)
    render_build_script(CLONE_PATH, build_required, sha)

if __name__ == "__main__":
    main()
