'''
Combine the data csv's and explode out the nutrients column
'''

import pandas as pd
import pathlib
import yaml
import ast
import argparse

from featurize_ingredients import choose_top_grams, featurize_ingredients

def get_list(datasets):
    return [d.as_posix() for d in datasets]

def process_dataset_list(dfs):
    if len(dfs) > 0:
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
        
    # if empty
    return pd.DataFrame()

def agg_data(filter_ = False):
    dessert_drink = []
    sauces = []
    sides = []
    
    if filter_:
        dessert_datasets = pathlib.Path("../data").rglob("*dessert*.csv")
        beverage_datasets = pathlib.Path("../data").rglob("*beverage*.csv")
        side_datasets = pathlib.Path("../data").rglob("*side*.csv")
        snack_datasets = pathlib.Path("../data").rglob("*snack*.csv")
        bake_datasets = pathlib.Path("../data").rglob("*bakery*.csv")
        
        dessert_drink.extend(get_list(dessert_datasets))
        dessert_drink.extend(get_list(beverage_datasets))
        dessert_drink.extend(get_list(bake_datasets))

        sides.extend(side_datasets)
        sides.extend(snack_datasets)
        

    # find all 'csv' files in the data folder
    datasets = pathlib.Path("../data").rglob("*.csv")
    datasets = [d.as_posix() for d in datasets]
    datasets = [d for d in datasets if 'all' not in d]
    
    print(f"{len(datasets)} datasets found")
    
    # concatenate 
    dfs = []
    for dataset in datasets:
        if dataset not in dessert_drink and dataset not in sauces and dataset not in sides:
            dfs.append(pd.read_csv(dataset))
    
    dessert_dfs = []
    for dataset in dessert_drink:
        dessert_dfs.append(pd.read_csv(dataset))
    
    sauces_dfs = []
    for dataset in sauces:
        sauces_dfs.append(pd.read_csv(dataset))
        
    sides_dfs = []
    for dataset in sides:
        sides_dfs.append(pd.read_csv(dataset))
        
    print(len(dfs), len(dessert_dfs), len(sauces_dfs), len(sides_dfs))
        
    return process_dataset_list(dfs), process_dataset_list(dessert_dfs), \
        process_dataset_list(sauces_dfs), process_dataset_list(sides_dfs)

def save_dfs(dfs_nutrient, name):
    if len(dfs_nutrient) > 0:
        url_index_mapping = dfs_nutrient[['url', 'title', 'index']]
        print(f'saving to clean_data/{name}_url_index_mapping.csv\n')
        url_index_mapping.to_csv(f'../clean_data/{name}_url_index_mapping.csv', index = False)
        print(f'saving to clean_data/{name}_recipes_nutrient.csv')
        dfs_nutrient.to_csv(f'../clean_data/{name}_recipes_nutrient.csv', index = False)
    
def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--foo', '-f', default = False, action = 'store_true')
    args = parser.parse_args()
    filter_ = args.foo
    
    suffix = ''
    if filter_:
        suffix = '_filter'
    
    mains_dfs_nutrient, desserts_dfs_nutrient, sauces_dfs_nutrient, sides_dfs_nutrient = agg_data(filter_)
    save_dfs(mains_dfs_nutrient, f'mains{suffix}')
    save_dfs(desserts_dfs_nutrient, f'desserts{suffix}')
    save_dfs(sauces_dfs_nutrient, f'sauces{suffix}')
    save_dfs(sides_dfs_nutrient, f'sides{suffix}')
        
#     print('saving to clean_data/url_index_mapping.csv\n')
#     main_url_index_mapping.to_csv('../clean_data/url_index_mapping.csv', index = False)
#     print('saving to clean_data/all_recipes_nutrient.csv')
#     all_dfs_nutrient.to_csv('../clean_data/all_recipes_nutrient.csv', index = False)

if __name__ == "__main__":
    main()