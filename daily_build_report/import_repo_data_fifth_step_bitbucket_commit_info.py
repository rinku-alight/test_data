import collections
import sys
from pandas.core.base import NoNewAttributesMixin
from requests.auth import HTTPBasicAuth
import requests
import json
import jmespath
import pprint
from datetime import datetime
import pandas as pd
import time
import os
import numpy as np

# for local testing only
DOCKER_CONTAINER = os.environ.get('DOCKER_CONTAINER', False)
print(f'Docker Container: {DOCKER_CONTAINER}')
if not DOCKER_CONTAINER:
    from dotenv import load_dotenv
    load_dotenv()

print('Getting Bitbucket detail data...')

# pretty print configuration
pp = pprint.PrettyPrinter(indent=4)

# jmespath configuration
jmes_option = jmespath.Options(dict_cls=collections.OrderedDict)


# functions
def get_date(unixtime):
    try:
        dt_object = datetime.fromtimestamp(unixtime / 1000)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return unixtime


def get_jira_links(jira_list):
    if not jira_list:
        return 'no Jira links'
    else:
        url_list = []
        s = " "
        for j in jira_list:
            jurl = 'https://jira.alight.com/browse/{}'.format(j)
            # j_url = '<a href="{href}">{name}</a>'.format(href=jurl, name=j)
            url_list.append(jurl)
        return s.join(url_list)


def get_repo_data(repo_name, repo_name_service, project_name, project_key, data, search_criteria):
    repo_detail_list = jmespath.search(search_criteria, data, jmes_option)
    if repo_detail_list:
        last_commit = max(repo_detail_list, key=(
            lambda item: item[1]), default=(None, None))
        detail_dict = {"repo_name": repo_name,
                       "repo_name_service": repo_name_service,
                       "project_name": project_name,
                       "project_key": project_key,
                       "committer": last_commit[0],
                       "commit_date": get_date(last_commit[1]),
                       "commitId": last_commit[2],
                       "jira-key": last_commit[3],
                       "jira-links": get_jira_links(last_commit[3])}
        return detail_dict
    else:
        return None


def get_pullrequest_data(repo_detail_dict):
    api_get_url = repo_detail_dict['project_key'] +  \
        '/repos/' + repo_detail_dict['repo_name_service'] + \
        '/commits/' + repo_detail_dict['commitId'] + '/pull-requests'

    bb_url = base_url + api_url_base + api_get_url
    # print(bb_url)
    # print('Submitting request...')
    res = requests.get(bb_url, headers=headers, auth=auth)
    # print('Response received')
    if res.status_code != 200:
        # print('Status code: ' + str(res.status_code))
        return 'Unknown'

    data = res.json()
    # pp.pprint(data)
    search_criteria = 'values[].links.self[].href'
    repo_detail_list = jmespath.search(search_criteria, data, jmes_option)
    return str(repo_detail_list[0])


def get_api_data(base_url, api_url_base, project_key, repo_name, query_str):
    api_get_url = project_key + '/repos/' + repo_name + '/commits/'
    bb_url = base_url + api_url_base + api_get_url + query_str
    print(bb_url)
    r = requests.get(bb_url, headers=headers, auth=auth, proxies=proxies)
    return r


def check_url(project_key, repository_slug):
    search_crit_dict = {
        "filename": "values[*].path.name"
    }
    search_list = list(search_crit_dict.values())
    translation = {39: None}
    search_criteria = 'children.' + str(search_list).translate(translation)
    key_list = list(search_crit_dict.keys())

    api_url_base = 'rest/api/1.0/projects/' + project_key
    api_get_url = '/repos/' + repository_slug + '/browse/postman'

    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(user_name, bb_token)
    bb_url = base_url + api_url_base + api_get_url
    response = requests.get(bb_url, headers=headers,
                            auth=auth, proxies=proxies)
    if response.status_code != 200:
        print('Postman Search Status code: ' + str(response.status_code))
        return None
    else:
        print('Found valid postman list...')
        json_data = response.json()
        # pp.pprint(json_data)
        detail_list = get_detail_data(json_data, search_criteria)
        # pp.pprint(detail_list)
        return detail_list


def get_detail_data(data, search_criteria):
    # print(f'Search criteria: {search_criteria}')
    detail_list = jmespath.search(search_criteria, data, jmes_option)
    if detail_list:
        return detail_list[0]
    else:
        return None


def get_postman_url(src_url):
    postman_url = src_url.replace("pull-requests", "browse")
    url = postman_url.split('/')
    url_new = '/'.join(url[:-1] + ['postman'])
    # print(f'postman url: {url_new}')
    return url_new


# init parameters
bb_token = os.environ.get('BB_TOKEN')
user_name = os.environ.get('BB_USERNAME')
base_url = os.environ.get('BB_BASE_URL')
headers = {"Accept": "application/json"}
auth = HTTPBasicAuth(user_name, bb_token)
proxies = {
    'http': 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228',
    'https': 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
}
# get project data
bb_project_info_csv = 'data/bitbucket_repo_project_info_last_30_days.csv'
col_names = ['index', 'repo_name',
             'bitbucket_project_key', 'bitbucket_project_name']
repo_data = pd.read_csv(bb_project_info_csv, names=col_names, header=1)

pd.set_option('display.max_columns', None)
print(repo_data.head())


repo_detail_data = []

for index, row in repo_data.iterrows():
    repo_name = row['repo_name']
    project_name = row['bitbucket_project_name']
    project_key = row['bitbucket_project_key']
    api_url_base = 'rest/api/1.0/projects/'
    query_str = ''
    repo_name_service = repo_name
    response = get_api_data(base_url, api_url_base,
                            project_key, repo_name_service, query_str='')
    if response.status_code != 200:
        print('Status code: ' + str(response.status_code))

        repo_name_service = repo_name + '-service'
        print('Attempting service call for' + repo_name_service)
        response = get_api_data(base_url, api_url_base,
                                project_key, repo_name_service, query_str='')
        if response.status_code != 200:
            continue
        else:
            print('Got data with service extension')
    else:
        print('Got data for ' + repo_name_service)
    json_data = response.json()
    repo_detail_info = get_repo_data(repo_name, repo_name_service, project_name, project_key, json_data,
                                     'values[*].[author.displayName, authorTimestamp, id, properties."jira-key"]')
    # pp.pprint(repo_detail_info)
    if repo_detail_info:
        pr_href = get_pullrequest_data(repo_detail_info)
        repo_detail_info['pullrequest_url'] = str(pr_href)
        if repo_detail_info:
            repo_detail_data.append(repo_detail_info)
    time.sleep(1)

df = pd.DataFrame(repo_detail_data)

# add test detail information
df['postman_url'] = df.apply(
    lambda row: get_postman_url(row.pullrequest_url), axis=1)
df['test_files'] = df.apply(lambda row: check_url(
    row.project_key, row.repo_name_service), axis=1)
df['test_available'] = np.where(df['test_files'].isnull(), 'no', 'yes')

df_p1 = df.filter(['repo_name', 'postman_url', 'test_files'])
df_p1 = df_p1[df_p1['test_files'].notna()]
df_postman = df_p1.explode('test_files')


path = 'data/bitbucket_repo_detail_info_last_30_days.csv'
df.to_csv(path, index=False)
path = 'data/bitbucket_repo_postman_files.csv'
df_postman.to_csv(path, index=False)

print('Bitbucket Detail data collection finished')
