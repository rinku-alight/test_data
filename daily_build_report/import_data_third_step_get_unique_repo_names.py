import pandas as pd

print('Generating unique repo name list...')
import_path = 'data/repo_info_dtr_tst_last_30_days.csv'
df = pd.read_csv(import_path)
repo_names = df.repo_name

df_repos = repo_names.to_frame()
df_repos = pd.DataFrame.drop_duplicates(df_repos)


# export to csv
export_path = 'data/repo_names_last_30_days.csv'
df_repos.to_csv(export_path)

print('Export complete')
