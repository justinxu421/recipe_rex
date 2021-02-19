import pandas as pd
import numpy as np
from save_recipes import agg_data

# get the numerical amount of nutrient if not null, else return null
# ensure that the length of the field is 2 (number / unit)
def parse_nutrient(x):
    if not pd.isnull(x):
        d = x.split()
        assert(len(x.split()) == 2)
        return float(d[0])
    return x
            
def filter_nutrient(x, cutoff):
    if pd.isnull(x):
        return np.nan
    else:
        return x > cutoff
    
def featurize_nutrients(all_dfs_nutrient, save = False):
    nutrient_cols = [c for c in all_dfs_nutrient.columns if 'Content' in c]
    
    # select url and nutritional columns
    df = all_dfs_nutrient[['url'] + nutrient_cols].copy()
    df[nutrient_cols] = df[nutrient_cols].applymap(parse_nutrient)
    
    # filter for 75th percentile of of these nutrients

    df['high_carb'] = df['carbohydrateContent'].map(lambda x: filter_nutrient(x, 40))
    df['high_protein'] = df['proteinContent'].map(lambda x: filter_nutrient(x, 28))
    df['high_fat'] = df['fatContent'].map(lambda x: filter_nutrient(x, 25))
    df['high_sodium'] = df['sodiumContent'].map(lambda x: filter_nutrient(x, 1000))
    df['high_sugar'] = df['sugarContent'].map(lambda x: filter_nutrient(x, 9))
    df = df.set_index('url')
    # drop the original columns
    df = df.drop(columns = nutrient_cols)
    
    if save:
        df.to_csv('clean_data/nutrient_features.csv', index = True)
    
    return df