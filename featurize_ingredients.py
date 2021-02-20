import pandas as pd
import numpy as np
from collections import defaultdict
import ast
import re

# Get the most popular ingredients
def is_digit(word):
    return any(map(str.isdigit, word))

def is_paren(word):
    return "(" in word or ")" in word or "[" in word or "]" in word

# Rules that don't work
# a unit following a number (if i != 0 and is_digit(words[i-1]):)
# -- most are relevant like Chinese or leek
# small words (elif len(word) <= 4:)
# -- most are informative like Cai, Buns, Crab, Corn
# conclusion: allow the noise, including 5 spellings of jalapeno

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
    bigrams = [" ".join(unigrams[i:i+2]) for i in range(num_bi)]
    return bigrams

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

    print(f"Using {len(top_unigram_cts)} unigrams that occur over {min_unigram_ct} times")
    print(f"Using {len(top_bigram_cts)} bigrams that occur over {min_bigram_ct} times")
    
    # Create one hot encoding index for each gram
    top_grams = list(top_unigram_cts.keys()) + list(top_bigram_cts.keys())
    gram2idx = {gram : labelid for labelid, gram in enumerate(top_grams)}
    
    return top_unigram_cts, top_bigram_cts, gram2idx

def one_hot_encode_raw_ingrs(ingrs, gram2idx):
    label = np.zeros(len(gram2idx))
    grams = set()
    
    # collect all grams
    for ingr in ingrs:
        unigrams = get_unigrams(ingr)
        bigrams = get_bigrams(unigrams)    
        grams.update(unigrams)
        grams.update(bigrams)
    
    # one hot encode top occurring grams
    for gram in grams:
        if gram in gram2idx:
            idx = gram2idx[gram]
            label[idx] = 1
    
    return label

def featurize_ingredients(dataset: pd.DataFrame, save = False):
    _, _, gram2idx = choose_top_grams(dataset) 

    # Encode unigram/bigram ingredient vectors for each recipe
    ing_features = np.array([
            one_hot_encode_raw_ingrs(ingrs, gram2idx)
            for ingrs in dataset["ingredients"]
        ])

    ing_df = pd.DataFrame(ing_features, index = dataset['url'])
    if save:
        print('saving to clean_data/ing_features.csv\n')
        ing_df.to_csv('clean_data/ing_features.csv')

    return ing_df