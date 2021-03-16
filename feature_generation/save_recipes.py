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

        # remove urls with missing images
        missing_urls = ['https://www.justonecookbook.com/borscht-soup-hong-kong-style/',
                        'https://www.justonecookbook.com/easy-homemade-granola/',
                        'https://www.spicetheplate.com/veggie/sauteed-yam-soy-sauce/']
        all_dfs_nutrient = all_dfs_nutrient[~all_dfs_nutrient.url.isin(missing_urls)]

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

def transform_features(dfs_nutrient):
    dfs_nutrient.loc[dfs_nutrient['total_time'] > 120, 'total_time'] = 120
    dfs_nutrient['num_ingredients'] = dfs_nutrient['ingredients'].apply(len)
    return dfs_nutrient

def save_dfs(dfs_nutrient, folder, name):
    if len(dfs_nutrient) > 0:

        # save indices based on all mapping
        if folder == 'all':
            dfs_nutrient = transform_features(dfs_nutrient)
            url_index_mapping = dfs_nutrient[['url', 'title', 'index', 'total_time', 'num_ingredients']]
            url_index_mapping['title'] = url_index_mapping['title'].str.capitalize()

            print(f'saving to clean_data/{folder}/{name}_url_index_mapping.csv\n')
            url_index_mapping.to_csv(f'../clean_data/{folder}/{name}_url_index_mapping.csv', index = False)
        # if filter, then read from the all_url mapping we just saved
        else:
            all_url_index_mapping = pd.read_csv('../clean_data/all/all_url_index_mapping.csv', index_col = 'url')
            url_index_mapping = all_url_index_mapping.loc[dfs_nutrient['url'].values]

            print(f'saving to clean_data/{folder}/{name}_url_index_mapping.csv\n')
            url_index_mapping.to_csv(f'../clean_data/{folder}/{name}_url_index_mapping.csv', index = True)


        print(f'saving to clean_data/{folder}/{name}_recipes_nutrient.csv')
        dfs_nutrient.to_csv(f'../clean_data/{folder}/{name}_recipes_nutrient.csv', index = False)
    
def main():
    all_dfs_nutrient, _, _, _ = agg_data(False)
    mains_dfs_nutrient, desserts_dfs_nutrient, sauces_dfs_nutrient, sides_dfs_nutrient = agg_data(True)

    save_dfs(all_dfs_nutrient, 'all', 'all')
    save_dfs(mains_dfs_nutrient, 'mains', 'mains_filter')
    save_dfs(desserts_dfs_nutrient, 'desserts', 'desserts_filter')
    save_dfs(sauces_dfs_nutrient, 'sauces', 'sauces_filter')
    save_dfs(sides_dfs_nutrient, 'sides', 'sides_filter')
        
if __name__ == "__main__":
    main()