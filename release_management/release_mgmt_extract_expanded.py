import functools
import pprint
import pandas as pd
from jira import JIRA
import os
from decouple import config
import warnings
import re

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
DOCKER_CONTAINER = os.environ.get('DOCKER_CONTAINER', False)
print(f'Docker Container: {DOCKER_CONTAINER}')
if not DOCKER_CONTAINER:
    from dotenv import load_dotenv
    load_dotenv()

# configuration
jira_base_url = 'https://jira.alight.com/'

DATA_REPT_BASE = 'data'

username = os.environ.get('JIRA_USERNAME')
pwd = os.environ.get('JIRA_PWD')

print(f'username: {username}')
proxies = {
    'http': 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228',
    'https': 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
}

os.environ['http_proxy'] = 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
os.environ['https_proxy'] = 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
# pretty print configuration
pp = pprint.PrettyPrinter(indent=4)

# jira authentication
jira = JIRA(auth=(username, pwd), options={
            'server': jira_base_url, 'verify': False}, validate=True, proxies=proxies)

# functions


def get_detail_data(issue, search_criteria_dict):
    issue_list = []
    for k, v in search_criteria_dict.items():
        print(f'k: {k} v: {v}')
        attr = v
        print(f'Found issue attribute: {attr}')
        issue_list.append(k + ':' + attr)
    return issue_list


def convert_tuple(tup):
    str = ''.join(tup)
    return str


def get_dependencies(desc_text):
    svc_versions = []
    for line in desc_text.splitlines():
        try:
            mat = re.search(r'(Dependencies).*\|(.*)\|', line)
            if mat is not None:
                v = mat.group(2)
                version = v.encode('utf-8').decode('ascii', 'ignore')
                svc_versions.append(version)
        except ValueError:
            pass
    if not svc_versions:
        return 'N/A'
    return svc_versions


def get_service_versions(desc_text):
    svc_versions = []
    for line in desc_text.splitlines():
        try:
            mat = re.search(r'(Service Version\*\*)\|(.*)\|', line)
            if mat is not None:
                v = mat.group(2)
                version = v.encode('utf-8').decode('ascii', 'ignore')
                svc_versions.append(version)
        except ValueError:
            pass
    if not svc_versions:
        return 'N/A'
    return svc_versions


def get_scrutiny_urls(desc_text, search_tup):

    for line in desc_text.splitlines():
        try:
            mat = re.search(r'(Scrutiny Approval Link\*\*)\|(.*)\|', line)
            if mat is not None:
                v = mat.group(2)
                desc = v.encode('utf-8').decode('ascii', 'ignore')
                return get_url_list(desc, search_tup)
        except ValueError:
            pass
    return 'N/A'


def get_url_list(desc_text, search_tup):
    url_list = []
    for line in desc_text.splitlines():
        url = extract_url(line, search_tup)
        if url:
            # print(f'Found url: {url}')
            url_list.append(url)
    if url_list:
        ret_list = list(set(url_list))
        return ret_list
    else:
        return None


def extract_url(line, search_tup):
    regex = '(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?'
    urllist = []
    urllist = re.findall(
        r'(http|ftp|https)(:\/\/)([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?', line)
    # pp.pprint(urllist)
    if urllist:
        url_list = []
        for val in urllist:
            for item in val:
                if any(s in item for s in search_tup):
                    url_list.append(convert_tuple(val))
        if url_list:
            ret_list = list(set(url_list))
            return ret_list[0]
        else:
            return None
    else:
        return None


def get_service_names(url_list):
    if url_list:
        service_names = []
        for item in url_list:
            sn = get_service_name(item)
            if sn:
                service_names.append(sn)
        svc_list = list(set(service_names))
        return svc_list
    return None


def get_service_name(repo_url):
    service_name = None
    s_list = repo_url.split('/')
    try:
        service_name = s_list[s_list.index('repos') + 1]
        # print(f'service_name: {service_name}')
        return service_name
    except ValueError as ve:
        # print(f'Got ValueError: {ve}')
        return None


def rgetattr(obj, attr, *args):
    def __getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(__getattr, [obj] + attr.split('.'))


def get_field_data(field, name):
    return rgetattr(field, name, 'Not Populated')


def get_validation_fields(issue):
    migr_fields = issue.fields
    field_dict = {
        'migration_status': get_field_data(migr_fields, 'customfield_21600.value'),
        'QA_tester_email': get_field_data(migr_fields, 'customfield_12300.name'),
        'QA_tester_displayname': get_field_data(migr_fields, 'customfield_12300.displayName'),
        'migration_approver_email': get_field_data(migr_fields, 'customfield_17832.name'),
        'migration_approver_displayname': get_field_data(migr_fields, 'customfield_17832.displayName'),
        'scrutiny_tickets': get_field_data(migr_fields, 'customfield_22200')
    }
    valid_ticket = True
    jira_validation_results = {}
    for k, v in field_dict.items():
        if v is None:
            jira_validation_results[k] = 'Not Populated'
            valid_ticket = False
        # print(f'k: {k} v: {v}')
        fieldname = k
        attr = v
        if isinstance(attr, str):
            jira_validation_results[fieldname] = attr
        if isinstance(attr, list):
            count = 0
            keys = []
            for item in attr:
                fname = fieldname + '_' + str(count) + '_key'
                keys.append(item.key)
                jira_validation_results[fname] = item.key
                fname = fieldname + '_' + str(count) + '_url'
                jira_validation_results[fname] = item.self
                count = count + 1
            jira_validation_results[fieldname] = ', '.join(keys)
    jira_validation_results['valid_ticket'] = valid_ticket
    return jira_validation_results


jql = 'project = ADAMIGR AND issuetype = Epic AND status = Open ORDER BY createdDate'
proj_issues = []
print('Extracting epics...')
for issue in jira.search_issues(jql, maxResults=50):
    # issue_list = issue.fields()
    # print(*issue_list, sep="\n")

    issue_func_dict = {
        'key': issue.key,
        'issue_id': issue.id,
        'project': issue.fields.project.name,
        'status': issue.fields.status.name,
        'issue_type': issue.fields.issuetype.name,
        'create_date': issue.fields.created,
        'update_date': issue.fields.updated,
        'summary': issue.fields.summary
    }
    # print('{}: {}'.format(issue.key, issue.fields.summary))
    issue_list = {}
    for key in issue_func_dict:
        f = issue_func_dict.get(key)
        res = f
        issue_list[key] = str(res)

        # print(f'result: {res}')
    proj_issues.append(issue_list)

print('All Migration Ticket Extraction complete.')

df_proj = pd.DataFrame.from_dict(proj_issues)
df_proj = df_proj[df_proj['issue_type'] == 'Epic']
df_proj["create_date"] = pd.to_datetime(
    df_proj["create_date"], format="%Y-%m-%d")
df_proj["update_date"] = pd.to_datetime(
    df_proj["update_date"], format="%Y-%m-%d")

path = DATA_REPT_BASE + '/ada_migr_ticket_epic_list.csv'
df_proj.to_csv(path, index=False)
print('All Migration Ticket Extraction written to CSV file.')

epic_link_list = df_proj['key'].tolist()
pp.pprint(epic_link_list)

epic_link_issues = []
print('Extracting stories per epic...')
for epic_link in epic_link_list:
    jql = '"Epic Link"=' + epic_link
    for issue in jira.search_issues(jql, maxResults=50):
        # issue_list = issue.fields()
        # print(*issue_list, sep="\n")
        issue_func_dict = {
            'key': get_field_data(issue, 'key'),
            'issue_id': get_field_data(issue, 'id'),
            'issue_parent_ticket': get_field_data(issue, 'fields.customfield_10008'),
            'issue_rest_url': get_field_data(issue, 'self'),
            'assignee': get_field_data(issue, 'fields.assignee.displayName'),
            'reporter': get_field_data(issue, 'fields.reporter.displayName'),
            'status': get_field_data(issue, 'fields.status.name'),
            'issue_type': get_field_data(issue, 'fields.issuetype.name'),
            'resolution_description': get_field_data(issue, 'fields.status.description'),
            'create_date': get_field_data(issue, 'fields.created'),
            'update_date': get_field_data(issue, 'fields.updated'),
            'summary': get_field_data(issue, 'fields.summary'),
            'description': get_field_data(issue, 'fields.description')
        }
        # print('{}: {}'.format(issue.key, issue.fields.summary))
        issue_list = {}
        for k, v in issue_func_dict.items():
            if v is None:
                issue_list[k] = 'Not Populated'
            fieldname = k
            attr = v
            if isinstance(attr, str):
                issue_list[fieldname] = attr
        # add jira ticket validation here

        validation_results = get_validation_fields(issue)
        issue_list.update(validation_results)
        # print(f'result: {res}')
        epic_link_issues.append(issue_list)


print('Epic Link Issue Extraction complete.')

df = pd.DataFrame.from_dict(epic_link_issues)
df = df[df['issue_type'] == 'Story']
df["create_date"] = pd.to_datetime(df["create_date"], format="%Y-%m-%d")
df["update_date"] = pd.to_datetime(df["update_date"], format="%Y-%m-%d")
df['dependencies'] = df.apply(
    lambda row: get_dependencies(row.description), axis=1)

path = DATA_REPT_BASE + '/current_rel_epic_data.csv'
df.to_csv(path, index=False)

print('Exiting after test...')
# sys.exit(0)
search_tup = ('MIG-')

df['scrutiny_url'] = df.apply(
    lambda row: get_scrutiny_urls(row.description, ('MIG-')), axis=1)
df['pull_requests'] = df.apply(lambda row: get_url_list(
    row.description, ('pull-requests')), axis=1)
df['service_version'] = df.apply(
    lambda row: get_service_versions(row.description), axis=1)
df['services'] = df.apply(
    lambda row: get_service_names(row.pull_requests), axis=1)
df.drop(['description'], axis=1, inplace=True)

df2 = df.explode('services')
df2a = df2.explode('service_version')
df3 = df2a.explode('pull_requests')
df4 = df3.explode('scrutiny_url')
df4.drop(['issue_rest_url', 'assignee', 'status', 'resolution_description', 'create_date',
         'update_date', 'status', 'reporter', 'summary', 'issue_type', 'dependencies'], axis=1, inplace=True)

path = DATA_REPT_BASE + '/ada_migr_ticket_data.csv'
df4.to_csv(path, index=False)

print('Job complete')
