import json
import pandas as pd
import pprint
import datetime as dt

# pretty print configuration
pp = pprint.PrettyPrinter(indent=4)

# functions


def get_build_type(name, version, digest, repo_dict):
    if 'snapshot' in version.lower():
        return 'snapshot'
    elif 'latest' in version.lower():
        d = repo_dict.get(name)
        for item in d:
            #             pp.pprint(item)
            v = item.get('version')
            if 'snapshot' in v.lower():
                #                 pp.pprint(item)
                d = item.get('digest')
                #                 print(d)
                if d == digest:
                    #                     print('found digest')
                    return 'snapshot'
        return 'release'
    return 'release'


print('Data conversion started...')
path = 'data/artifactory_repo_info.json'
with open(path) as json_file:
    repo_data = json.load(json_file)

repo_name_list = list(repo_data.keys())
# pp.pprint(repo_name_list)

# consolidate data

latest_list = []
for name in repo_name_list:
    version_data_list = repo_data.get(name)
    for version in version_data_list:
        build_type = get_build_type(name, version.get(
            'version'), version.get('digest'), repo_data)
        latest_list.append([name, version.get('version'), version.get(
            'create_date'), version.get('update_date'), version.get('digest'), build_type])

idx = ['repo_name', 'version', 'create_date',
       'update_date', 'digest', 'build_type']
df = pd.DataFrame(latest_list, columns=idx)

# set dates to datetime
df["create_date"] = pd.to_datetime(df["create_date"], format="%Y-%m-%d")
df["update_date"] = pd.to_datetime(df["update_date"], format="%Y-%m-%d")
# set to date only
df["create_date"] = df["create_date"].dt.date
df["update_date"] = df["update_date"].dt.date

# set current date
current_date = pd.to_datetime(dt.datetime.now())
df = df.set_index('update_date')
df = df.sort_index()


# reindex to last 30 days only
df = df.loc[current_date - pd.Timedelta(days=30):current_date].reset_index()

# sort update date desc
df.sort_values("update_date", inplace=True, ascending=False)

# export to csv
export_path = 'data/repo_info_dtr_tst_last_30_days.csv'
df.to_csv(export_path)

print('CSV Export finished')
