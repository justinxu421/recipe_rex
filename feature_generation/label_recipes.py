import ast
import numpy as np
import pandas as pd
    
def label_meat(ing, include, exclude):    
    for i_ in ing:
        i_ = i_.lower()
        # check if any meats are present in ingredient
        for meat in include:
            if meat in i_:
                # check if all excluded terms are not present too
                if all([e not in i_ for e in exclude]):
                    return 1
    return 0

def label_all_meats(ing, label_names):
    poultry = ['chicken', 'turkey', 'duck', 'quail', 'thigh', 'breast']
    beef = ['beef', 'steak', 'ribeye', 'sirloin', 'oxtail', 'brisket', 'bison', 'dog', 'gyoza', 'lamb']
    pork = ['pork', 'bacon', 'ham', 'sausage', 'dog', 'spam', 'rib', 'pastrami', 'prosciutto']
    fish = ['fish', 'tilapia', 'salmon', 'cod', 'flounder', 'tuna', 'sardine', 'barramundi', 'branzino', 'porgies', 'bass']
    seafood = ['shrimp', 'octopus', 'oysters', 'clam', 'abalone', 'squid', 'calamari', 'seafood', 'crab', 'lobster', 'mussel', 'scallop', 'snail']
    exclude = ['chicken stock', 'fish sauce']
    
    poultry_ = label_meat(ing, poultry, exclude)
    beef_ = label_meat(ing, beef, exclude)
    pork_ = label_meat(ing, pork, exclude)
    fish_ = label_meat(ing, fish, exclude)
    seafood_ = label_meat(ing, seafood, exclude)

    label_map = {
        'poultry': poultry_,
        'beef': beef_,
        'pork': pork_,
        'fish': fish_,
        'seafood': seafood_,
    }

    all_labels = []
    for label in label_names:
        all_labels.append(label_map[label])
    
    # vegeterian is not any
    veg = int(not any(all_labels))
    all_labels.append(veg)
    return all_labels

def get_meat_labels(main_recipes, folder, label_names, save = False):
    main_ing = main_recipes['ingredients'].apply(ast.literal_eval)

    meat_labels = []
    for ing in main_ing:
        meat_labels.append(label_all_meats(ing, label_names))

    meat_labels = np.array(meat_labels)
    meat_label_df = pd.DataFrame(meat_labels, index = main_recipes['url'], columns = label_names + ['veg'])
    
    if save:
        print(f'saving to clean_data/{folder}/meat_label.csv\n')
        meat_label_df.to_csv(f'../clean_data/{folder}/meat_labels.csv')

    return meat_label_df

def label_starch(ing, include, exclude):    
    for i_ in ing:
        i_ = i_.lower()
        # check if any meats are present in ingredient
        for meat in include:
            if meat in i_:
                # check if all excluded terms are not present too
                if all([e not in i_ for e in exclude]):
                    return 1
    return 0

def label_soup(ing, title):
    soup = ['cups chicken broth', 'cups vegetable stock', 'cups chicken stock']
    soup_ = label_starch(ing, soup, [])
    if soup_ or ('soup' in title.lower() and 'soup dumpling' not in title.lower()):
        return 1
    return 0
    
def label_all_starches(ing, title, label_names):
    noodle = ['noodle', 'vermicelli']
    rice = ['rice']
    stew = ['curry', 'stew', 'garam masala']
    exclude = ['rice wine', 'rice vinegar', 'rice powder', 'rice noodle', 'vermicelli']
    
    noodle_ = label_starch(ing, noodle, [])
    rice_ = label_starch(ing, rice, exclude)
    soup_ = label_soup(ing, title)
    stew_ = label_starch(ing, stew, exclude)

    label_map = {
        'noodle': noodle_,
        'rice': rice_,
        'soup': soup_,
        'stew': stew_,
    }

    all_labels = []
    for label in label_names:
        all_labels.append(label_map[label])

    none = int(not any(all_labels))
    all_labels.append(none)
    
    return all_labels

def get_starch_labels(main_recipes, folder, label_names, save = False):
    main_ing = main_recipes['ingredients'].apply(ast.literal_eval)

#     start_index, last_index = 0, 2000
#     for i, (title, ing) in enumerate(zip(main_recipes['title'][start_index:last_index], main_ing[start_index:last_index])):
#         labels = label_all_starches(ing, title)
# #         if labels[-2] == 1 and 'soup' not in title.lower():
#         print(i, labels, title)

    starch_labels = []
    for title, ing in zip(main_recipes['title'], main_ing):
        starch_labels.append(label_all_starches(ing, title, label_names))

    starch_labels = np.array(starch_labels)
    starch_labels_df = pd.DataFrame(starch_labels, index = main_recipes['url'], columns = label_names + ['none'])
    
    if save:
        print(f'saving to clean_data/{folder}/starch_label.csv\n')
        starch_labels_df.to_csv(f'../clean_data/{folder}/starch_labels.csv')

    return starch_labels_df

def main():
    main_recipes = pd.read_csv('../clean_data/mains/mains_filter_recipes_nutrient.csv')
    get_meat_labels(main_recipes, 'mains', ['poultry', 'beef', 'pork', 'fish', 'seafood'], save = True)
    get_starch_labels(main_recipes, 'mains', ['noodle', 'rice', 'soup', 'stew'], save = True) 
    
    dessert_recipes = pd.read_csv('../clean_data/desserts/desserts_filter_recipes_nutrient.csv')
    get_meat_labels(dessert_recipes, 'desserts', [], save = True)
    get_starch_labels(dessert_recipes, 'desserts', [], save = True) 
    
    sides_recipes = pd.read_csv('../clean_data/sides/sides_filter_recipes_nutrient.csv')
    get_meat_labels(sides_recipes, 'sides', [], save = True)
    get_starch_labels(sides_recipes, 'sides', [], save = True) 

if __name__ == "__main__":
    main()