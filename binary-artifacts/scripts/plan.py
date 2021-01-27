import os

from jinja2 import Template
from git import Repo

from build_utils import load_json_file, get_s3_client

GIT_REPO = os.environ['GIT_REPO']
GIT_BRANCH = os.environ.get('GIT_BRANCH', 'main')
CLONE_PATH = os.environ.get('CLONE_PATH', '/opt/repo')

BUILD_LIST_PATH = os.environ.get('BUILD_LIST_PATH', '/opt/build_list/build_list.json')

S3_ENDPOINT = os.environ['S3_ENDPOINT']
S3_REGION = os.environ['S3_REGION']
S3_ACCESS_KEY = os.environ['S3_ACCESS_KEY']
S3_SECRET_KEY = os.environ['S3_SECRET_KEY']

def setup_repo(repo_url, branch, path):
    repo = Repo.clone_from(repo_url, path)
    repo.git.checkout(branch)
    return repo

def is_build_required(s3_client, build_list, commit_sha):
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
    with open('/opt/scripts/RUN_BUILD.sh.j2') as f:
        tmpl = Template(f.read())
        build_file_path = os.path.join(repo_path, "RUN_BUILD.sh")
        with open(build_file_path, "w+") as f2:
            f2.write(tmpl.render(run_build = build_required, sha = commit_sha, clone_path = repo_path))
        os.chmod(build_file_path, 555)

if __name__ == "__main__":
    repo = setup_repo(GIT_REPO, GIT_BRANCH, CLONE_PATH)
    sha = repo.head.commit.hexsha
    build_list = load_json_file(BUILD_LIST_PATH)
    s3_client = get_s3_client(
        S3_ENDPOINT,
        S3_REGION,
        S3_ACCESS_KEY,
        S3_SECRET_KEY
    )
    build_required = is_build_required(s3_client, build_list, sha)
    render_build_script(CLONE_PATH, build_required, sha)