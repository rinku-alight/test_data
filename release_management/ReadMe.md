# Summary

The Release Management Report is designed to create a series of CSV output files that represent ADA Migration Epics and the associated stories for each release identified as an epic in Jira.

There is a single script that generates three CSV files for consumption in Power BI

## Container Build

There is not a containerized version of this at this time. The script executes fairly quickly and would be a good candidate for a serverless function initiated on a schedule in AWS

### Dependencies
- pandas
