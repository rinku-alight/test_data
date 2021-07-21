#!/bin/bash
set -e
cd /home/appuser
echo "Running test script..."

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

run_script "test.py"