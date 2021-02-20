import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# read from csv 
# drop nas
# scale to standard
def process_embeddings(file):
    df = pd.read_csv(f'clean_data/{file}', index_col = 'url')    
    df = df.dropna()
    
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)
    df_scaled = pd.DataFrame(scaled, index = df.index)
    return df_scaled
    
# get neighbors based on euclidean distance
def fit_knn(df):    
    model_knn = NearestNeighbors(algorithm='brute', n_neighbors=20, n_jobs=-1)
    model_knn.fit(df)
    return model_knn

# given indices for df, find the nearest neighbors
def get_neighbors_knn(df, indices, num_neighbors = 10):
    model_knn = fit_knn(df)

    # get x based on the index
    x = df.iloc[indices].to_numpy()
    dists, neighbors = model_knn.kneighbors(x, num_neighbors)
    
    # return urls, the distances, and the nearest neighbors
    return df.index[indices], dists, neighbors

# get the indices for the df based on urls
def get_df_indices(df, urls):
    reset_df = df.reset_index()
    indices = reset_df[reset_df['url'].isin(urls)].index
    return indices

# find the nearest neighbors to the average of the inputs
def get_recs_knn_average(df, urls, num_neighbors = 10):
    indices = get_df_indices(df, urls)
    
    # build knn model
    model_knn = fit_knn(df)

    # get x based on the index
    x = df.iloc[indices].to_numpy().mean(axis = 0).reshape((1, -1))
    dists, neighbors = model_knn.kneighbors(x, num_neighbors)
    
    # return urls, the distances, and the nearest neighbors
    return df.index[indices], df.index[neighbors[0]]

# generate recs by candidate generation -> ranking
def get_recs_knn(df, urls, num_neighbors = 10):  
    indices = get_df_indices(df, urls)
    
    # candidate generation
    candidates = set()
    urls_, dists_, neighbors_ = get_neighbors_knn(df, indices, num_neighbors)
    for url, d, n in zip(urls_, dists_, neighbors_):
        valid_n = n
        candidates |= set(valid_n)
    candidates = list(candidates)
        
    # rank the candidates by adding distances
    candidate_dists = []
    for candidate in candidates:
        total_dist = 0
        for index in indices:
            total_dist += np.sum((df.iloc[index].to_numpy() - df.iloc[candidate])**2)
        candidate_dists.append((candidate, total_dist))
        
    # sort candidates by total distance
    sorted_candidates = sorted(candidate_dists, key = lambda x: x[1])
    top_10 = [c for c,d in sorted_candidates[:10]]
    top_10_dist = [d for c,d in sorted_candidates[:10]]
    
    return urls, df.index[top_10]
