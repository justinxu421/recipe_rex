'''
Combine the data csv's and explode out the nutrients column
'''

import pandas as pd
import pathlib
import yaml
import ast

from featurize_ingredients import choose_top_grams, featurize_ingredients


def agg_data():
    # find all 'csv' files in the data folder
    datasets = pathlib.Path("../data").rglob("*.csv")
    datasets = [d.as_posix() for d in datasets]
    datasets = [d for d in datasets if 'all' not in d]
    print(f"{len(datasets)} datasets found")
    
    # concatenate 
    dfs = []
    for dataset in datasets:
        dfs.append(pd.read_csv(dataset))
    all_dfs = pd.concat(dfs)
    
    all_dfs['nutrients'] = all_dfs['nutrients'].apply(lambda x: yaml.safe_load(x))
    nutrient_df = pd.DataFrame(all_dfs['nutrients'].values.tolist(), index = all_dfs.index)
    all_dfs_nutrient = pd.concat([all_dfs, nutrient_df], axis = 1)
    all_dfs_nutrient = all_dfs_nutrient.drop(columns = ['nutrients'])
    
    # make unique index for each recipe
    all_dfs_nutrient = all_dfs_nutrient.drop_duplicates()
    all_dfs_nutrient = all_dfs_nutrient.reset_index().drop(columns = 'index')
    print(f"number of recipes {len(all_dfs_nutrient)}")
    
    # convert stringified ingredients array to List
    all_dfs_nutrient["ingredients"] = all_dfs_nutrient["ingredients"].apply(lambda ingr: ast.literal_eval(ingr))

    return all_dfs_nutrient.reset_index()

def main():
    all_dfs_nutrient = agg_data()
    url_index_mapping = all_dfs_nutrient[['url', 'title', 'index']]
    
    print('saving to clean_data/url_index_mapping.csv\n')
    url_index_mapping.to_csv('../clean_data/url_index_mapping.csv', index = False)
    print('saving to clean_data/all_recipes_nutrient.csv')
    all_dfs_nutrient.to_csv('../clean_data/all_recipes_nutrient.csv', index = False)

if __name__ == "__main__":
    main()