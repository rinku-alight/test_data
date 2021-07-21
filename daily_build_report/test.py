import os
print('Test script execution started...')

user_name = os.environ.get('USERNAME')
jira_user = os.environ.get('JIRA_USER')
bb_user = os.environ.get('BB_USERNAME')
bb_base = os.environ.get('BB_BASE_URL')


print(f'Username is {user_name}')
print(f'Jira user is {jira_user}')
print(f'BB User is {bb_user}')
print(f'BB Base is {bb_base}')



print('Test script execution complete')