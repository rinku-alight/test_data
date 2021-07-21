import pprint
import re
import os
from requests.auth import HTTPBasicAuth
import requests
from bs4 import BeautifulSoup
import re
import datetime as dt
import pandas as pd

# for local testing only
DOCKER_CONTAINER = os.environ.get('DOCKER_CONTAINER', False)
print(f'Docker Container: {DOCKER_CONTAINER}')
if not DOCKER_CONTAINER:
    from dotenv import load_dotenv
    load_dotenv()

#configuration
pp = pprint.PrettyPrinter(indent=4)

print('Starting scan import...')
username = os.environ.get('JIRA_USER')
pwd = os.environ.get('JIRA_PWD')
server = os.environ.get('FILE_SERVER')
print(f'user: {username}')
proxies = {
    'http' : 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228',
    'https' : 'http://proxyuser:proxypass@proxycachest.hewitt.com:3228'
}

# pretty print configuration
pp = pprint.PrettyPrinter(indent=4)
# base configuration
headers = {"Accept": "text/html",
            "Content-Type": "text/html"}
auth = HTTPBasicAuth(username, pwd)
base_request_url = 'http://' + server + '/'
print(f'request_url: {base_request_url}')

def extract_date(input_field):
    date_val = None
    # print(f'Checking input field {input_field}')
    if not input_field:
        return None
    try:
        mat = re.search(r'\b(\d+-\S+-\d{4})', input_field)
        if mat is not None:
            ext_date = mat.group(1)
            # print(f'Found match {ext_date}')
            date_val = get_datetime(mat.group(1))
    except ValueError:
        pass
    return date_val

# functions
def get_datetime(date_str):
    try:
        d = dt.datetime.strptime(date_str,"%d-%b-%Y")
        return d.date()
    except ValueError:
        return None
    
def get_folder_info(base_url, output_file=None):
    print(f'Opening base url: {base_url}')
    index_data = ''
    response = requests.get(base_url, headers=headers, auth=auth, verify=False)
    if response.status_code != 200:
        print(f'Status code: {response.status_code}')
    else:
        # print('Got data valid response')
        index_data = response.content
        #write content to local file
        if output_file:
            f = open(output_file, 'w')
            f.write(str(index_data))
            f.close()
            print('Output written to file')

    # response.close()
    # print('connection closed')
    # pp.pprint(index_data[0:20])
    return get_index_list(index_data)
    
def get_index_list(index_data):
    soup = BeautifulSoup(index_data, 'html.parser')
    all_a = soup.select('a')
    index_list = []
    for tag in all_a:
        anchor_text = tag['href']
        if(len(anchor_text) > 5):
            sib = tag.next_sibling
            n = []
            n.append(anchor_text.replace('/',''))
            n.append(extract_date(sib))
            index_list.append(n)

    return index_list

def get_scan_results(scan_file_text):
    pattern = re.compile(r'((High|Medium|Low) severity results):\s(\d+)')
    sev_list = []
    for line in scan_file_text.splitlines():
        for match in re.finditer(pattern, line):
            if match is not None:
                d = {match.group(1): match.group(3)}
                sev_list.append(d)
    if sev_list:
        return sev_list
    else:
        return None
   

def get_service_scan_results(service_name):
    dir_list = get_folder_info(base_request_url + service_name, output_file=None)
    scan_res_list = []
    # pp.pprint(dir_list[0:5])
    if dir_list:
        max_folder_name = max(dir_list, key=lambda x: x[1])[0]
        output_file = 'output/' + max_folder_name + '.html'
        file_list = get_folder_info(base_request_url + service_name + '/' + max_folder_name)

        if any('scan.txt' in sublist for sublist in file_list):
            link = base_request_url + service_name + '/' + max_folder_name + '/scan.txt'
            f_in = requests.get(link)
            scan_res_list = get_scan_results(f_in.text)
    return scan_res_list


# local testing -- remove
# service_name = 'channel-umaclient-service'
# scan_res_list = get_service_scan_results(service_name)
# pp.pprint(scan_res_list)


# start processing
output_file = 'data/index_data.html'
index_list = get_folder_info(base_request_url, output_file)
if not index_list:
    print('No data retrieved')
    os.sys.exit(0)

pp.pprint(index_list[0:5])
df = pd.DataFrame (index_list, columns=['service', 'update_date'])

# filter on data less than 30 days old
current_date = pd.to_datetime(dt.datetime.now())
df = df.set_index('update_date')
df = df.sort_index()

# reindex to last 30 days only
df = df.loc[current_date - pd.Timedelta(days=30):current_date].reset_index()

# sort update date desc
df.sort_values("update_date", inplace=True, ascending=False)
# get sub folders
df['sec_scan_results'] = df.apply(lambda row: get_service_scan_results(row.service), axis=1)
df_p1 = df.filter(['service','sec_scan_results'])
df_p1 = df_p1[df_p1['sec_scan_results'].notna()]
df_scan = df_p1.explode('sec_scan_results')
df_scan = df_scan[df_scan['sec_scan_results'].notna()]

df_scan = pd.concat([df_scan.drop(['sec_scan_results'], axis=1), df_scan['sec_scan_results'].apply(pd.Series)], axis=1)
df_scan = df_scan.fillna(0).reindex()

path = 'data/build_logs_last_30_days.csv'
df.to_csv(path, index = False)
path = 'data/scan_results_last_30_days.csv'
df_scan.to_csv(path, index = False, header=None)

# get new dataframe from scan results
# get repo list data
scan_results_csv = 'data/scan_results_last_30_days.csv'
col_names = ['service','High severity results','Medium severity results','Low severity results']
df1 = pd.read_csv(scan_results_csv, names=col_names, header=None)
df1['High severity results'] = pd.to_numeric(df1['High severity results'])

# aggregate
aggregation_functions = {'High severity results': 'sum', 'Medium severity results': 'sum', 'Low severity results': 'sum'}
df_new = df1.groupby(df1['service']).agg(aggregation_functions)

path = 'data/scan_results_agg_last_30_days.csv'
df_new.to_csv(path)

# cleanup intermediate files
cleanup_files = ['data/index_data.html','data/scan_results_last_30_days.csv']
for f in cleanup_files:
    if os.path.isfile(f):
        os.remove(f)

print('Scan processing complete')