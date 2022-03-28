import requests
import os 
import functools
import json
from dotenv import load_dotenv, find_dotenv
from decouple import config
from requests.auth import HTTPBasicAuth
from jira import  JIRA
import pandas as pd 
load_dotenv(find_dotenv())

username = os.environ.get('JIRA_USER_LOCAL')
pwd = os.environ.get('JIRA_TOKEN_LOCAL')
jira_url = os.environ.get('BASE_URL')

def fetched_data():
    jira = JIRA(basic_auth=(username, pwd), options={'server':jira_url, 'verify':False}, validate=False)

    # functions
    def rgetattr(obj, attr, *args):
        def __getattr(obj, attr):
            return getattr(obj, attr, *args)
        return functools.reduce(__getattr, [obj] + attr.split('.'))

    def get_field_data(field, name):
        return rgetattr(field, name, 'Not Populated')
    
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

    # extracting issues from tickets

    epic_link_list = df_proj['key'].tolist()
    #print(epic_link_list)

    epic_link_issues = []
    validation_issues = []
    print('Extracting issues...')
    for epic_link in epic_link_list:
        jql = '"Epic Link"=' + epic_link
        for issue in jira.search_issues(jql, maxResults=50):
            # issue_list = issue.fields()        
            # print(*issue_list, sep="\n")
            issue_func_dict = {
                'key': get_field_data(issue, 'key'),
                'issue_id': get_field_data(issue, 'id'),
                'issue_parent_ticket': get_field_data(issue, 'fields.parent.key'),
                'issue_parent_ticket_summary': get_field_data(issue, 'fields.parent.fields.summary'),
                'issue_rest_url': get_field_data(issue, 'self'), #issue.self,
                'assignee': get_field_data(issue, 'fields.assignee.displayName'), #issue.fields.assignee.displayName,
                'reporter': get_field_data(issue, 'fields.reporter.displayName'), #issue.fields.reporter.displayName,
                'status': get_field_data(issue, 'fields.status.name'), #issue.fields.status.name,
                'issue_type': get_field_data(issue, 'fields.issuetype.name'), #issue.fields.issuetype.name,
                'resolution_description': get_field_data(issue, 'fields.status.description'), #issue.fields.status.description,
                'create_date': get_field_data(issue, 'fields.created'), #issue.fields.created,
                'update_date': get_field_data(issue, 'fields.updated'), #issue.fields.updated,
                'summary': get_field_data(issue, 'fields.summary'), #issue.fields.summary,
                'description': get_field_data(issue, 'fields.description'), #issue.fields.description
                'service_name': get_field_data(issue, 'fields.customfield_10320'), 
                'mig_req_url': get_field_data(issue, 'fields.customfield_10321'), 
                'dev_approved_by': get_field_data(issue, 'fields.customfield_10251'), 
                'qa_test_approved_by': get_field_data(issue, 'fields.customfield_10252'), 
                'int_test_approved_by': get_field_data(issue, 'fields.customfield_10327'), 
                'dev_approved': get_field_data(issue, 'fields.customfield_10234'), 
                'new_docker_secrets': get_field_data(issue, 'fields.customfield_10325.value'),
                'qa_test_script_approved': get_field_data(issue, 'fields.customfield_10237'), 
                'ace_migration_status': get_field_data(issue, 'fields.customfield_10238.value'),
                'migration_approved_by': get_field_data(issue, 'fields.customfield_10252.displayName.value'),  

                
            }
            # print('{}: {}'.format(issue.key, issue.fields.summary))
            issue_list = {}
            for key in issue_func_dict:
                f = issue_func_dict.get(key)
                res = f
                issue_list[key] = str(res)

                # print(f'result: {res}')
            epic_link_issues.append(issue_list)
        
    print('Epic Link Issue Extraction complete.')

    df = pd.DataFrame.from_dict(epic_link_issues)

    def get_type(input_val):
        if input_val:
            if 'None' in input_val:
                return 'None'
            if 'Yes' in input_val:
                return 'Yes'
            if 'No' in input_val:
                return 'No'

    df['dev_approved'] = df['dev_approved'].apply(get_type)
    df['qa_test_script_approved'] = df['qa_test_script_approved'].apply(get_type)
    return df

#Function to create a df according to lifecycle
def life_df(org_df, lifecyle=""):
    comp_life = "Ready for " + lifecyle.upper() + " migration"
    #print(comp_life)
    mask = org_df['ace_migration_status'] == comp_life
    if any(mask) == True:
        new_df = org_df.loc[mask]
        return new_df
    else:
        print("This lifecyle does'nt match with any row of dataframe")


def create_df_with_busrule(org_df, bus_rules, lifecycle=""):
    with open(bus_rules, "r") as json_file:
        bus_rule_dict =json.load(json_file)
    
    if lifecycle in bus_rule_dict.keys():
        
        comp_life = "Ready for " + lifecycle.upper() + " migration"
        #print(comp_life)

        mask = org_df['ace_migration_status'] == comp_life
        if any(mask) == True:
            new_df = org_df.loc[mask]
            
            def validate_row_value(df_row):
                val_list = bus_rule_dict.get(lifecycle)
                if val_list is not None:
                    # print(val_list)
                    for row_name in val_list:
                        if 'None' in df_row[row_name]:
                            return False          
                    return True
                else:
                    print('No business rules defined for this lifecycle')
            new_df['validate_ticket'] = new_df.apply(lambda row: validate_row_value(row), axis=1)
            return new_df
            
        else:
            print("This lifecyle does'nt match with any row of dataframe")
    else:
        print("This business does not match with any lifecycle")


