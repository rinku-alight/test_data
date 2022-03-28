import pandas as pd
import json
import collections
import re


def create_df(json_obj):
    with open(json_obj, "r") as json_file:
        json_data = json.load(json_file)
    
    final_dict = {'lifecycle':[], 'service_name':[], 'service_version':[]}
    for i in range(0, len(json_data)):
        final_dict['lifecycle'].append(json_data[i]['Spec']['Name'].partition("-")[0])
        final_dict['service_name'].append(re.split(':|/alight/|/|\*|\n', json_data[i]['Spec']['TaskTemplate']['ContainerSpec']['Image'])[1])
        final_dict['service_version'].append(json_data[i]['Spec']['TaskTemplate']['ContainerSpec']['Image'].partition(":")[2])
    
    df = pd.DataFrame(final_dict)
    return df