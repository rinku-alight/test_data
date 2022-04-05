import pandas as pd
import json
import collections
import re
from functools import reduce

with open('services_list_example.json', "r") as json_file:
    json_data = json.load(json_file)


def create_df(field_names):
    new_dict = {i: [] for i in field_names.keys()}
    for k, v in field_names.items():
        for i in range(0, len(json_data)):
            v_list= v.split(".")
            actual_data = reduce(dict.get, v_list, json_data[i])
            #print(actual_data)
            new_dict[k].append(actual_data)

    #creating data frame by new_dict
    df = pd.DataFrame(new_dict)
    
    # Fuction for filter lifecycle field fo data frame
    def life_cycle(colm):
        filt_list = []
        for i in colm:
            if '-' in i :
                k=i.split("-",1)[0]
                filt_list.append(k)
            else:
                filt_list.append(i)
        return filt_list
    life_list = life_cycle(df['lifecycle'])
    df['lifecycle']=life_list

    # Fuction for filter service_name field fo data frame
    def servi_name(rows):
        filt_list=[]
        for i in rows:
            if 'alight/' in i :
                k=re.split(':|/alight/|/|\*|\n', i)[1]
                filt_list.append(k)
            else:
                k=i.split(':', 1)[0]
                filt_list.append(k)
        return filt_list

    ser_name = servi_name(df['service_name'])
    df['service_name']=ser_name

    # Fuction for filter service_version field fo data frame
    def service_ver(colm):
        filt_lst = []
        for i in colm:
            if ':' in i :
                k=i.split(":")[1]
                filt_lst.append(k)
            else:
                filt_lst.append(i)
        return filt_lst
    serv_ver = service_ver(df['service_version'])
    df['service_version']=serv_ver
    return df