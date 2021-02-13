'''
Combine the data csv's and explode out the nutrients column
'''

import pandas as pd
import pathlib
import yaml

def agg_data():
    # find all 'csv' files in the data folder
    datasets = pathlib.Path("data").rglob("*.csv")
    datasets = [d.as_posix() for d in datasets]
    datasets = [d for d in datasets if 'all' not in d]
    print(f"{len(datasets)} datasets found")
    
    # concatenate 
    dfs = []
    for dataset in datasets:
        dfs.append(pd.read_csv(dataset))
    all_dfs = pd.concat(dfs)
    
    all_dfs['nutrients'] = all_dfs['nutrients'].apply(lambda x: yaml.load(x))
    nutrient_df = pd.DataFrame(all_dfs['nutrients'].values.tolist(), index = all_dfs.index)
    all_dfs_nutrient = pd.concat([all_dfs, nutrient_df], axis = 1)
    all_dfs_nutrient = all_dfs_nutrient.drop(columns = ['nutrients'])
    
    return all_dfs_nutrient

def main():
    all_dfs_nutrient = agg_data()
    all_dfs_nutrient.to_csv('data/all_recipes_nutrient.csv')

if __name__ == "__main__":
    main()