#!/bin/bash
set -e

#set proxy
export HTTP_PROXY=http://proxyuser:proxypass@proxycachest.hewitt.com:3228
export HTTPS_PROXY=http://proxyuser:proxypass@proxycachest.hewitt.com:3228
export DOCKER_CONTAINER=True

cd /home/appuser

run_script()
{
    python3 $1
    exit_code=$?
    if [[ $exit_code -ne 0 ]];
    then
        echo "Exit $exit_code from $1"
        exit $exit_code
    else
        echo "$1 successfully executed"
    fi
}

echo "Running test..."

run_script "test.py"

echo "Testing complete"

echo "Running import jobs..."

run_script "import_repo_data_first_step.py"
run_script "import_repo_data_second_step_generate_csv.py"
run_script "import_data_third_step_get_unique_repo_names.py"
run_script "import_repo_data_fourth_step_bitbucket_project_info.py"
run_script "import_repo_data_fifth_step_bitbucket_commit_info.py"
run_script "import_sec_scan_data_sixth_step.py"


# copy results to mounted volume
if [[ -d "/home/appuser/output" ]];
then
    echo "Mounted volume found"
    rm -f /home/appuser/output/*.*
    cp /home/appuser/data/*.* /home/appuser/output/
else
    echo "Output directory not found"
fi

echo "Jobs completed"