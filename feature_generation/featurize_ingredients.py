import pandas as pd
import numpy as np
from collections import defaultdict
import ast
import re
import os
import time
from pathlib import Path
import pickle
import fasttext
import fasttext.util

MAIN_DIR = Path("..")

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

def load_non_ing_grams(path):
    with open(path, "rb") as f:
        grams_to_exclude_dict = pickle.load(f)
    
    print(f"Loaded non ingredient grams to filter out from {path.as_posix()}")
    
    grams_to_exclude = [
        gram
        for gram, indicator in grams_to_exclude_dict.items() 
        if indicator == "0" # FIXME: easily misunderstood as int 0
    ]
    
    original_num = len(grams_to_exclude_dict)
    included_num = original_num - len(grams_to_exclude)
    print(f"Left with {included_num} ingredient grams / {original_num} total grams")
    
    return grams_to_exclude

def remove_non_ing_grams(top_unigram_cts, top_bigram_cts):
    unigrams_to_exclude_path = MAIN_DIR / "clean_data" / "all" / "non_ing_unigrams_dict.pkl"
    bigrams_to_exclude_path = MAIN_DIR / "clean_data" / "all" / "non_ing_bigrams_dict.pkl"
    
    unigrams_to_exclude = load_non_ing_grams(unigrams_to_exclude_path)    
    bigrams_to_exclude = load_non_ing_grams(bigrams_to_exclude_path)
    
    included_unigram_cts = {
        gram : ct 
        for gram, ct in top_unigram_cts.items() 
        if gram not in unigrams_to_exclude
    }
    
    included_bigram_cts = {
        gram : ct 
        for gram, ct in top_bigram_cts.items() 
        if gram not in bigrams_to_exclude
    }
    
    return included_unigram_cts, included_bigram_cts

def choose_top_grams(
    dataset: pd.DataFrame, 
    min_unigram_ct = 20, 
    min_bigram_ct = 20,
    exclude_non_ing = True,
):
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
    
    if exclude_non_ing: # replace uni/bigram ct dicts
        top_unigram_cts, top_bigram_cts = remove_non_ing_grams(top_unigram_cts, top_bigram_cts)
    
    # Create one hot encoding index for each gram
    top_grams = list(top_unigram_cts.keys()) + list(top_bigram_cts.keys())
    gram2idx = {gram : labelid for labelid, gram in enumerate(top_grams)}
    
    return top_unigram_cts, top_bigram_cts, gram2idx

def get_inv_freq_average(gram_embeddings, ing_gram_probs, embedding_dim, alpha=1e-3):
    """
    Gets sentence embeddings by averaging weighted by inverse frequency
    
    :param gram_embeddings: dict mapping grams to their fasttext embeddings
    :param ing_gram_probs: dict mapping ingredient grams to their proportion of occurence
    """
    
    weighted_embeddings = [
        alpha / (alpha + ing_gram_probs[gram]) * embedding
        for gram, embedding in gram_embeddings.items()
    ]
    
    if not weighted_embeddings:
        # This recipe has no uni/bigrams that are ingredients
        # e.g. because of recipe scraper limitations, such as
        # https://www.eatingthaifood.com/toasted-rice-powder-recipe/
        # has [1, 5, 0, , g, r, a, m, s, , s, t, i, c, k, y, ...]
        return np.zeros(embedding_dim)
        
    average_embedding = np.mean(weighted_embeddings, axis=0)
    assert average_embedding.shape == (embedding_dim,)
    
    return average_embedding

def get_gram_embedding(gram, ft):
    """
    Gets fasttext embedding for each gram. For bigrams, embeddings for the
    individual words are averaged.
    
    :param gram: uni/bigram string
    :param ft: fasttext word embedding model
    """
    embeddings = [ft[word] for word in gram.split(" ")]
    embedding = np.mean(embeddings, axis=0) 

    assert embedding.shape == (300,)
    return embedding

def load_fasttext_model(embedding_dim=300):
    """
    Loads the fasttext model.
    
    :param embedding_dim: the embedding dimension, must be <= 300
    """
    
    if not os.path.exists("cc.en.300.bin"):
        print("Downloading fasttext cc english language model. May take 1-2 hours.")
        fasttext.util.download_model('en', if_exists='ignore')
        print("Download complete")
    
    print("Loading model into memory ... ")
    tic = time.time()
    
    ft = fasttext.load_model("cc.en.300.bin")
    fasttext.util.reduce_model(ft, embedding_dim)
    
    print(f"Loaded model in {(time.time() - tic)/60 : .2f} min")
    
    return ft
    
def extract_ing_grams(raw_ingrs, all_ing_grams):
    """
    :param raw_ingrs: list of ingredient descriptions
    :param ingr_grams: list of grams that are valid ingredients
    :return: list of ingredient uni/bigrams
    """
    # Collect all grams
    grams = set()
    for ingr in raw_ingrs:
        unigrams = get_unigrams(ingr)
        bigrams = get_bigrams(unigrams)    
        grams.update(unigrams)
        grams.update(bigrams)
    
    # Filter out non ingredient grams
    grams = grams & set(all_ing_grams)
    
    return list(grams)
    
def get_sentence_embeddings(
    dataset, 
    ing_gram_cts,
    embedding_dim=300,
):
    """
    Creates a "sentence embedding" for a recipe's ingredients list 
    by 1) getting fasttext embeddings for ingredient unigrams and
    bigrams and 2) averaging them using inverse frequency weights
    
    Inverse frequency modeled off SIF. TODO subtract away the first principal component of all sentence vectors
    
    :param dataset: 
    :param ing_gram_cts: dict of ingredient unigrams and bigrams and their frequencies
    :return: sentence embedding for the ingredient
    """
    
    # Download fasttext model
    ft = load_fasttext_model(embedding_dim)
    
    # Get gram embeddings
    all_gram_embeddings = {
        gram : get_gram_embedding(gram, ft) 
        for gram in ing_gram_cts.keys()
    }
    
    # Get gram probabilities for sentence embeddings
    total_cts = np.sum(list(ing_gram_cts.values()))
    
    ing_gram_probs = {
        gram : ct / total_cts
        for gram, ct in ing_gram_cts.items()
    }
    
    # Get all ingredient grams for extracting from raw ingredients
    all_ing_grams = list(ing_gram_cts.keys())
    
    # Get sentence embeddings
    sentence_embeddings = {}
    for url, raw_ingrs in zip(dataset.url, dataset.ingredients):
        print(url)
        grams = extract_ing_grams(raw_ingrs, all_ing_grams)
        
        gram_embeddings = {
            gram : all_gram_embeddings[gram]
            for gram in grams
        }
        
        sentence_embeddings[url] = get_inv_freq_average(
            gram_embeddings, 
            ing_gram_probs,
            embedding_dim,
        )
    
    # Save to dataframe
    return pd.DataFrame.from_dict(sentence_embeddings, orient="index")


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
#    # One hot encoding
#     _, _, gram2idx = choose_top_grams(dataset, exclude_non_ing=True) 

#     # Encode unigram/bigram ingredient vectors for each recipe
#     ing_features = np.array([
#             one_hot_encode_raw_ingrs(ingrs, gram2idx)
#             for ingrs in dataset["ingredients"]
#         ])

#     ing_df = pd.DataFrame(ing_features, index = dataset['url'])
    
    # Fasttext embeddings
    ing_unigram_cts, ing_bigram_cts, _ = choose_top_grams(dataset, exclude_non_ing=True)
    
    ing_gram_cts = {
        gram : ct 
        for gram, ct in 
        list(ing_unigram_cts.items()) + list(ing_bigram_cts.items())
    }
    
    assert len(ing_gram_cts) == len(ing_unigram_cts) + len(ing_bigram_cts)
    
    ing_df = get_sentence_embeddings(dataset, ing_gram_cts)

    if save:
        print('saving to clean_data/ing_features.csv\n')
        ing_df.to_csv('../clean_data/ing_features.csv')

    return ing_df