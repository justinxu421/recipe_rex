import pandas as pd
import numpy as np
from collections import defaultdict
import re
import ast
import pickle
import os
from gensim.models import KeyedVectors
import gensim.downloader as api

GRAM2VEC_PATH = "data/gram2vec.pkl"

def is_digit(word):
    return any(map(str.isdigit, word))

def is_paren(word):
    return "(" in word or ")" in word or "[" in word or "]" in word

def get_unigrams(ingr: str):
    unigrams = []
    
    words = re.split("[,/.;:\- ]", ingr) # split on spaces and punctuation
    for i, word in enumerate(words):
        if is_digit(word) or is_paren(word) or len(word) <= 2: 
            # exclude
            continue
        
        unigrams.append(word)
    
    return unigrams

def get_bigrams(unigrams: list):
    num_bi = len(unigrams) - 1
    bigrams = ["_".join(unigrams[i:i+2]) for i in range(num_bi)]
    return bigrams

def get_gram2vec(grams):
    if os.path.exists(GRAM2VEC_PATH):
        # Load mapping
        with open(GRAM2VEC_PATH, "rb") as f:
            gram2vec = pickle.load(f)
        return gram2vec
    
    # Create mapping from pretrained word2vec
    path = api.load("word2vec-google-news-300", return_path=True)
    word2vec = KeyedVectors.load_word2vec_format(path, binary=True)
    
#     print(word2vec.index2word[:30])
    valid_grams = list(set(grams) & set(word2vec.index2word))
    assert len(valid_grams) <= len(grams)
    print(f"{len(valid_grams)} of {len(grams)} grams mapped to an embedding")
    
    return {gram : word2vec[gram] for gram in valid_grams}


def choose_top_grams(dataset: pd.DataFrame, min_unigram_ct = 20, min_bigram_ct = 20):
    # Collect all possible uni/bigrams
    unigram_cts, bigram_cts = defaultdict(lambda: 0), defaultdict(lambda: 0)
    
    # if string embedding, convert to list
    if type(dataset['ingredients'][0]) == str:
        dataset['ingredients'] = dataset['ingredients'].apply(ast.literal_eval)
        
    for ingr_list in dataset["ingredients"]:
        for ingr in ingr_list:
            unigrams = get_unigrams(ingr)
            bigrams = get_bigrams(unigrams)

            for gram in unigrams:
                unigram_cts[gram] += 1

            for gram in bigrams:
                bigram_cts[gram] += 1

    # Choose the top occurring grams
    top_unigram_cts = {gram : ct for gram, ct in unigram_cts.items() if ct >= min_unigram_ct}
    top_bigram_cts = {gram : ct for gram, ct in bigram_cts.items() if ct >= min_bigram_ct}
    gram_cts = {**top_unigram_cts, **top_bigram_cts}
#     print(gram_cts)
    
    print(f"Using {len(top_unigram_cts)} unigrams that occur over {min_unigram_ct} times")
    print(f"Using {len(top_bigram_cts)} bigrams that occur over {min_bigram_ct} times")
        
    # Map each gram valid in word2vec to a vector
    top_grams = list(gram_cts.keys())
    gram2vec = get_gram2vec(top_grams) # excludes grams not found in the loaded word2vec
    valid_gram_cts = {gram : gram_cts[gram] for gram in gram2vec.keys()}
    
    # Find probability of each valid gram
    total_ct = np.sum(list(valid_gram_cts.values()))
    gram_probs = {gram : ct / total_ct for gram, ct in valid_gram_cts.items()}
    assert np.isclose(np.sum(list(gram_probs.values())), 1)
    
    return gram_probs, gram2vec

def run_sif(ingrs, gram2vec, gram_probs, alpha=1e-3):
    # TODO: subtract away each sentence vec's component in the first singular vector u
    # TODO: tune alpha, using fse default
    
    # collect all grams
    grams = set()
    for ingr in ingrs:
        unigrams = get_unigrams(ingr)
        bigrams = get_bigrams(unigrams)    
        grams.update(unigrams)
        grams.update(bigrams)
        
    # consider only valid grams found in word2vec
    # around half of grams are filtered out
    grams = grams & gram2vec.keys()
            
    # inverted probability weight
    weighted_gram_vecs = []
    
    for gram in grams:
        weighted_gram_vecs.append(
            alpha / (alpha + gram_probs[gram]) * np.array(gram2vec[gram])
        )
    
    sentence_vec = np.sum(np.array(weighted_gram_vecs), axis=0)
    sentence_vec /= len(ingrs)
    
    return sentence_vec

def featurize_ingredients(dataset: pd.DataFrame, save = False):
    gram_probs, gram2vec = choose_top_grams(dataset) 

    # Encode unigram/bigram ingredient vectors for each recipe
    ing_features = np.array([
        run_sif(ingrs, gram2vec, gram_probs)
        for ingrs in dataset["ingredients"]
    ])
    
    ing_df = pd.DataFrame(ing_features, index = dataset['url'])
    if save:
        ing_df.to_csv('clean_data/ing_features_sif.csv')
        
    return ing_df
