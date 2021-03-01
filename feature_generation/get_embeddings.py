import pandas as pd
import numpy as np

from featurize_nutrition import featurize_nutrients
from featurize_ingredients import featurize_ingredients
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

file_name = 'embeddings_main_filter'
folder = 'mains'

def compress(ing_df, components = 5):
    pca = PCA(components)
    ing_pca = pca.fit_transform(ing_df.to_numpy())
    ing_pca_df = pd.DataFrame(ing_pca, index = ing_df.index)
    return ing_pca_df

# read from csv 
# drop nas
# scale to standard
def process_embeddings(file, save = False):
    df = pd.read_csv(f'../clean_data/{folder}/{file_name}.csv', index_col = 'url')    
    df = df.dropna()
    
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)
    df_scaled = pd.DataFrame(scaled, index = df.index, columns = df.columns)
    
    if save:
        print(f'saving to clean_data/{folder}/{file_name}_scaled.csv\n')
        df_scaled.to_csv(f'../clean_data/{folder}/{file_name}_scaled.csv')
        
    return df_scaled

def get_embeddings(all_dfs_nutrient, load = True, save = False):
    # load nutrient df and then generate 
    if load:
        print('loading nutrient and ingredients from csv')
        nutrient_df = pd.read_csv(f'../clean_data/{folder}/nutrient_features.csv', index_col = 'url')
        ing_df = pd.read_csv(f'../clean_data/{folder}/ing_features.csv', index_col = 'url')
    else:
        nutrient_df = featurize_nutrients(all_dfs_nutrient, save = False)
        ing_df = featurize_ingredients(all_dfs_nutrient, save = False)
    
    # perform pca on ingredients df
    ing_pca_df = compress(ing_df, 5)
    embeddings_df = ing_pca_df.join(nutrient_df)
    
    if save:
        print(f'saving to clean_data/{folder}/{file_name}.csv\n')
        embeddings_df.to_csv(f'../clean_data/{folder}/{file_name}.csv')
    
    return embeddings_df

# load nutrients and save embeddings
def main():
#     all_dfs_nutrient = pd.read_csv(f'../clean_data/{folder}/all_recipes_nutrient.csv')
    all_dfs_nutrient = pd.read_csv(f'../clean_data/{folder}/mains_filter_recipes_nutrient.csv')
    
    # load and save nutrient df
    nutrient_df = featurize_nutrients(all_dfs_nutrient, save = True, folder = folder)
    # load and save ingredient df
    ing_df = featurize_ingredients(all_dfs_nutrient, save = True, folder = folder)
    
    # save the embeddings
    embeddings_df = get_embeddings(all_dfs_nutrient, load = True, save = True)
    
    # also save scaled version
    embeddings_df_scaled = process_embeddings(file_name, save = True)

if __name__ == "__main__":
    main()