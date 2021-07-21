import collections
import sys
from requests.auth import HTTPBasicAuth
import requests
import json
import jmespath
import pprint
from datetime import datetime
import pandas as pd
import os


# for local testing only
DOCKER_CONTAINER = os.environ.get('DOCKER_CONTAINER', False)
print(f'Docker Container: {DOCKER_CONTAINER}')
if not DOCKER_CONTAINER:
    from dotenv import load_dotenv
    load_dotenv()

print('Getting Bitbucket project data')

# pretty print configuration
pp = pprint.PrettyPrinter(indent=4)

#jmespath configuration
jmes_option = jmespath.Options(dict_cls=collections.OrderedDict)

# functions
def get_date(unixtime):
    try:
        dt_object = datetime.fromtimestamp(unixtime/1000)
        return  dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return unixtime

def get_repo_data(repo_name, data, search_criteria):
    repo_detail_list = jmespath.search(search_criteria, data, jmes_option)
    if repo_detail_list:
        detail_list = repo_detail_list[0]
        detail_dict = {"repo_name": repo_name,
                       "bitbucket_project_key": detail_list[0],
                       "bitbucket_project_name": detail_list[1]}
        return detail_dict
    else:
        return None

# init parameters
bb_token = os.environ.get('BB_TOKEN')
user_name = os.environ.get('BB_USERNAME')
base_url = os.environ.get('BB_BASE_URL')

# user_name = os.environ.get('JIRA_USER')
# bb_token = os.environ.get('JIRA_PWD')

proxies = {
    'http' : 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228',
    'https' : 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
}

headers = {"Accept": "application/json"}
auth = HTTPBasicAuth(user_name, bb_token)

# get repo list data
repo_name_csv = 'data/repo_names_last_30_days.csv'
col_names = ['index', 'repo_name']
repo_data = pd.read_csv(repo_name_csv, names=col_names)

repo_names = repo_data.repo_name.tolist()

# get repo commit info
# repo pattern

# /REST/API/1.0/PROJECTS?NAME&PERMISSION
# /rest/api/1.0/projects/{projectKey}
# /rest/api/1.0/repos
# /REST/API/1.0/REPOS?NAME&PROJECTNAME&PERMISSION&STATE&VISIBILITY

repo_detail_data = []
# repo_names = ['channel-accountlockwidgets-service','channel-content-service', 'yml-validator-service']
# project_key = 'UPN'

for repo_name in repo_names:
    api_url_base = 'rest/api/1.0/'
    api_get_url = 'repos'
    query_str = '?name=' + repo_name

    
    bb_url = base_url + api_url_base + api_get_url + query_str
    # print(bb_url)
    # print('Submitting request...')
    response = requests.get(bb_url, headers=headers, auth=auth, proxies=proxies)
    # print('Response received')
    if response.status_code != 200:
        print('Status code: ' + str(response.status_code))
        sys.exit(1)

    json_data = response.json()
    # pp.pprint(json_data)

    repo_detail_info = get_repo_data(repo_name, json_data, 'values[*].project.[key, name]')
    # pp.pprint(repo_detail_info)
    if repo_detail_info:
        repo_detail_data.append(repo_detail_info)


df = pd.DataFrame(repo_detail_data)
pp.pprint(df.head())
bb_project_info_csv = 'data/bitbucket_repo_project_info_last_30_days.csv'
df.to_csv(bb_project_info_csv)

print('Bitbucket project data collection finished')