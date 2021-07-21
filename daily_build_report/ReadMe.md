# Summary

The Daily Build Report is designed to create a series of CSV output files that represent aggregated data on the activities of the Adept Build process for ACE over the last 30 days.

The scripts themselves are a series of Python modules that execute within a container on demand.

## Container Build

The container should be built using the build_container.sh shell script in this folder. Alternatively, the container can be built with the following command:

> docker build . -t repo-data-collection

## Container Execution

Execution of the container as a standalone ephemeral service can be accomplished by executing the following command:

> docker-compose run repo-data run.sh

### Dependencies
- pandas
- pandas
- requests
- jmespath
- pprintpp
- numpy
- bs4