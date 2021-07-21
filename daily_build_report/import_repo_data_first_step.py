import collections
import sys
from requests.auth import HTTPBasicAuth
import requests
import json
import jmespath
import pprint
import time
import os

# for local testing only
DOCKER_CONTAINER = os.environ.get('DOCKER_CONTAINER', False)
print(f'Docker Container: {DOCKER_CONTAINER}')
if not DOCKER_CONTAINER:
    from dotenv import load_dotenv
    load_dotenv()

print('Starting Artifactory data collection... ')

# pretty print configuration
pp = pprint.PrettyPrinter(indent=4)

base_url = os.environ.get('ARTIFACTORY_BASE_URL')
api_url = '/api/v0/repositories/alight'
api_tag_url = '/api/v0/repositories/alight/test-template/tags'
query_str = '?pageStart=1&pageSize=300&count=false'
access_key = os.environ.get('ACCESS_KEY')
user_name = os.environ.get('USERNAME')

# jmespath configuration
jmes_option = jmespath.Options(dict_cls=collections.OrderedDict)


def get_filtered_data(json_data, search_criteria):
    return jmespath.search(search_criteria, data, jmes_option)


proxies = {
    'http': 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228',
    'https': 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
}

# default_headers = make_headers(proxy_basic_auth='')
# http = ProxyManager("http://proxycachest.hewitt.com:3228", headers=default_headers)
headers = {"Accept": "application/json"}
auth = HTTPBasicAuth(user_name, access_key)
print('Submitting request...')
try:
    response = requests.get(base_url + api_url + query_str,
                            headers=headers, auth=auth, proxies=proxies)
except OSError:
    print('OS Error')
    sys.exit(1)


print('Response received')
if response.status_code != 200:
    print('Status code: ' + str(response.status_code))
    sys.exit(1)
else:
    print('Got a good response')
    # sys.exit(0)

data = response.json()
# pp.pprint(data)
# json_data_str = json.dumps(data, indent=2)
# print(json_data_str)
# sys.exit(0)
repo_names = get_filtered_data(data, 'repositories[*].name')
# print(repo_names)

repo_data_dict = dict()
for repo_name in repo_names:
    repo_name_list = []
    api_tag_url = '/api/v0/repositories/alight/' + repo_name + '/tags'
    # print(api_tag_url)
    try:
        tag_resp = requests.get(
            base_url + api_tag_url + query_str, headers=headers, auth=auth, proxies=proxies)
    except OSError:
        print('OS Error')
        sys.exit(1)

    # print('Response received')
    if tag_resp.status_code != 200:
        print('Status code: ' + str(tag_resp.status_code))
    data = tag_resp.json()
    # print(json.dumps(data, indent=2))
    tag_data = get_filtered_data(
        data, '[*].[name, createdAt, updatedAt, digest]')

    tag_data_keys = ['version', 'create_date', 'update_date', 'digest']
    tag_data_list = []
    for item in tag_data:
        tag_data_dict = dict(zip(tag_data_keys, item))
        tag_data_list.append(tag_data_dict)

    repo_data_dict[repo_name] = tag_data_list
    print('Processed ' + repo_name)
    time.sleep(1)

# pp.pprint(repo_data_dict)

# write out the json data
path = 'data/artifactory_repo_info.json'
with open(path, 'w') as output_file:
    json.dump(repo_data_dict, output_file, indent=2)

print('Artifactory data collection finished')
sys.exit(0)
