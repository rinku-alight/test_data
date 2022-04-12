import re
import pytest
import json
import pandas as pd
from docker_swarm_mod import create_df

def test_create_df():
    #call function
    actual = create_df({'lifecycle':'Spec.Name', 'service_name': 'Spec.TaskTemplate.ContainerSpec.Image','service_version': 'Spec.TaskTemplate.ContainerSpec.Image'})

    #test expectattion 
    with open('services_list_example.json', "r") as json_file:
        json_data = json.load(json_file)

    final_dict = {'lifecycle':[], 'service_name':[], 'service_version':[]}
    for i in range(0, len(json_data)):
        final_dict['lifecycle'].append(json_data[i]['Spec']['Name'].partition("-")[0])
        final_dict['service_name'].append(re.split(':|/alight/|/|\*|\n', json_data[i]['Spec']['TaskTemplate']['ContainerSpec']['Image'])[1])
        final_dict['service_version'].append(json_data[i]['Spec']['TaskTemplate']['ContainerSpec']['Image'].partition(":")[2])

    expected = pd.DataFrame(final_dict)

    #assertion
    pytest.approx(actual, expected)