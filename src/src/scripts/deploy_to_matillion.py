import os
import logging
import requests
from requests.auth import HTTPBasicAuth
import argparse


def get_auth_object():
    return HTTPBasicAuth(os.environ.get('matillion_username'), os.environ.get('matillion_password'))


def get_matillion_url():
    return f"{os.environ.get('matillion_url')}/rest/v1/"


def __deploy_to_matillion(project_name, group_name, repository_url,branch_name):
    init_url = f'{get_matillion_url()}group/name/{group_name}/project/name/{project_name}/version/name/it_test/scm/clone'
    logging.info('Project Info URL: %s', init_url)
    commit_message = {
        "remoteURI": repository_url,
        "auth": {
            "authType": "HTTPS",
            "username": os.environ.get("git_username"),
            "password": os.environ.get("git_apikey")
        }
    }
    response = requests.post(init_url, auth=get_auth_object(), json=commit_message,verify=False)
    if response.status_code == 200:
        logging.warning("Initialized Remote Git: %s", response.json())
    else:
        logging.warning("Failed to initialize the Remote git: %s", response.text)

    sync_latest = f'{get_matillion_url()}group/name/{group_name}/project/name/{project_name}/scm/fetch'
    auth_data = {
        "auth": {
            "authType": "HTTPS",
            "username": os.environ.get("git_username"),
            "password": os.environ.get("git_apikey")
        },
        "fetchOptions": {
            "removeDeletedRefs": True,
            "thinFetch": False
        }
    }
    response = requests.post(sync_latest, auth=get_auth_object(), json=auth_data,verify=False)
    if response.status_code == 200:
        logging.warning("Sync Remote Repository: %s", response.json())
    else:
        logging.warning("Failed to Sync the repository: %s", response.text)
        raise Exception(f"Got Exception: {response.text}")

    get_commit_url = f'{get_matillion_url()}group/name/{group_name}/project/name/{project_name}/scm/getState'
    response = requests.get(get_commit_url, auth=get_auth_object(),verify=False)
    if response.status_code == 200:
        logging.warning("Commit status: %s", response.json())
    else:
        logging.warning("Commit Status Failed: %s", response.text)
        raise Exception(f"Got Exception: {response.text}")

    # latest_commit = response.json()['result']['commits'][0]['referenceID']
    commit_dict = response.json()['result']['commits']
    latest_commit = ''

    for commit in commit_dict:
        logging.info("Commit tag: %s",commit['tags'])
        for each_tag in commit['tags'] :
            if each_tag == {'type': 'REMOTE_HEAD', 'text': f'{branch_name}'} :
                latest_commit = commit['referenceID']
                break
        if latest_commit !="":
            break

    logging.info("latest_commit : %s", latest_commit)


    logging.info("Got latest commit id as: %s", latest_commit)

    switch_to_commit = f'{get_matillion_url()}group/name/{group_name}/project/name/{project_name}/version/name/it_test/scm/switchCommit'
    commit_data = {
        "commitID": latest_commit
    }
    response = requests.post(switch_to_commit, auth=get_auth_object(), json=commit_data,verify=False)
    if response.status_code == 200:
        logging.warning("Switched to latest commit: %s", response.json())
    else:
        logging.warning("Failed to switch to latest Commit: %s", response.text)
        raise Exception(f"Got Exception: {response.text}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    ## some test
    parser.add_argument('project_name', metavar='project_name', type=str, help='Project name in which the git to be sync')
    parser.add_argument('group_id',  metavar='group_id', type=str, help='Group name in which project is created')
    parser.add_argument('git_repo_url', metavar='git_repo_url', type=str, help='Git repository url')
    parser.add_argument('branch_name', metavar='branch_name', type=str, help='branch to checkout ')
    args = parser.parse_args()
    logging.info("Got project name as : %s", args.project_name)

    __deploy_to_matillion(args.project_name, args.group_id, args.git_repo_url,args.branch_name)
