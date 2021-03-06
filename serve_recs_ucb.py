import pandas as pd
import matplotlib.pyplot as plt
import math
import random

from get_recommendations_knn import get_recs_knn_average
from matplotlib import image 
from collections import defaultdict

class UCBRecSys():
    def __init__(self):
        # load embeddings and index map
        self.embeddings_df_scaled = pd.read_csv('clean_data/mains/embeddings_mains_filter_scaled.csv', index_col = 'url')
        self.url_index_mapping = pd.read_csv('clean_data/mains/mains_filter_url_index_mapping.csv', index_col = 'url')    

        self.meat_labels = pd.read_csv('clean_data/mains/meat_labels.csv', index_col = 'url').loc[self.embeddings_df_scaled.index]
        self.starch_labels = pd.read_csv('clean_data/mains/starch_labels.csv', index_col = 'url').loc[self.embeddings_df_scaled.index]
        # self.taste_labels = pd.read_csv('clean_data/mains/nutrient_features.csv', index_col = 'url')

        # flags for which axes to build filters/UCB for
        self.axes = ['meat', 'starch']

        # just set it to meats
        self.all_labels = {
                        'meat': self.meat_labels,
                        'starch': self.starch_labels,
                        }

        # initialize ucb parameters
        self.counts = {axis: {key: 0 for key in self.all_labels[axis]} for axis in self.axes}
        self.totals = {axis: {key: 0 for key in self.all_labels[axis]} for axis in self.axes}

    # get lower and upper confidence bounds
    def get_confidence_bounds(self, axis):
        bounds = {}
        total_counts = sum(self.counts[axis].values())
        for key in self.all_labels[axis].columns:
            # offset is calculated to figure out UCB
            offset = 0 if self.counts[axis][key] == 0 else math.sqrt((2 * math.log(total_counts)) / self.counts[axis][key]) 
            value = 0 if self.counts[axis][key] == 0 else self.totals[axis][key] / self.counts[axis][key]
            lower, upper = value - offset, value + offset
            bounds[key] = (lower, upper)

        return bounds

    # get the value
    def get_value_df(self, axis):
        bounds = self.get_confidence_bounds(axis) 
        conf_df = pd.DataFrame(bounds).T
        conf_df.columns = ['lower', 'upper']
        conf_df['val'] = (conf_df['lower'] + conf_df['upper']) / 2
        return conf_df['val']

    # select arm based on UCB criterion
    def select_axis_arm(self, axis):
        # make a selection if never selected
        for key in self.all_labels[axis].columns:
            if self.counts[axis][key] == 0:
                return key 

        ucb_values = {key: bound[1] for key, bound in self.get_confidence_bounds(axis).items()}

        # return arm with largest ucb
        max_ = max(ucb_values.values())
        for key in ucb_values:
            if ucb_values[key] == max_:
                return key

    # update our arms
    def update_counts(self, url, increment = 1):
        for axis in self.axes:
            for key, val in self.all_labels[axis].loc[url].items():
                if val == 1:
                    self.counts[axis][key] += increment

    # update totals after selection is made
    def update_values(self, url, choices, reward = 1):
        for axis in self.axes:
            # get counts of the current choices to figure out how much reward to add
            choice_counts = defaultdict(int)
            for url_ in choices:
                for key, val in self.all_labels[axis].loc[url_].items():
                    if val == 1:
                        choice_counts[key] += reward

            for key, val in self.all_labels[axis].loc[url].items():
                if val == 1:
                    self.totals[axis][key] += choice_counts[key]

    # based on the selected key arm and axis, pick a random url
    def get_random_url(self, key_dict):
        # pick a random axis to select url
        axis = random.choice(self.axes)
        label_df = self.all_labels[axis]
        key = key_dict[axis]
        key_urls = set(label_df[label_df[key] == 1].index)

        # sample a random url from this selected list
        return random.choice(list(key_urls))

    # randomly sample some urls and image paths
    def sample_urls(self, num_samples = 4, num_random = 1):
        keys = []

        # select how many random and how many greedy
        num_greedy = num_samples - num_random

        # select random key and random url
        for _ in range(num_random):
            key_dict = {}
            for axis in self.axes:
                key = random.choice(self.all_labels[axis].columns)
                key_dict[axis] = key
            keys.append(key_dict)

        # select random urls based on meats based on ucb, update with reward 1
        for _ in range(num_greedy):
            key_dict = {}
            for axis in self.axes:
                key = self.select_axis_arm(axis)
                key_dict[axis] = key
            keys.append(key_dict)

        urls = []
        for key_dict in keys:
            url = self.get_random_url(key_dict)
            self.update_counts(url)
            urls.append(url)
        print(keys)

        titles = self.url_index_mapping.loc[urls]['title'].values
        image_paths = self.get_image_paths(urls)
        
        return urls, titles, image_paths
    
    # plot 10 images given image paths
    def plot_images(self, image_paths):
        images = []
        for path in image_paths:
            img = image.imread(path)
            images.append(img)

        f, axarr = plt.subplots(2, 5, figsize = (20, 10))
        for i in range(10):
            a = i // 5
            b = i % 5
            axarr[a, b].imshow(images[i])

        f.tight_layout()
        plt.show()

    # get image paths from urls
    def get_image_paths(self, urls):
        return [f'images_resized/image_{index}.jpg' for index in self.url_index_mapping.loc[urls]['index']]

    # return a dictionary mapping top 10 urls and title and image index
    def get_recs(self, urls, value_cutoff = 0.5):
        # get filter based on selection criterion, and then find nearest neighbors
        filtered_urls = None

        for axis in self.axes:  
            filtered_urls_axis = set()
            conf_df = self.get_value_df(axis)

            # pick the ones with the 0.4 cutoff
            filters = conf_df[conf_df >= value_cutoff].index
            print(f'filters are {filters}')

            # union all relevant keys
            for key in filters:
                label_df = self.all_labels[axis]
                filtered_urls_axis |= set(label_df[label_df[key] == 1].index)

            # intersect the axes
            if filtered_urls is None:
                filtered_urls = filtered_urls_axis
            else:
                filtered_urls &= filtered_urls_axis

        # restrict to urls in embeddings df
        filtered_urls &= set(self.embeddings_df_scaled.index)

        _, rec_urls = get_recs_knn_average(self.embeddings_df_scaled.loc[filtered_urls], urls)
        rec_titles = self.url_index_mapping.loc[rec_urls]['title'].values
        rec_image_paths = self.get_image_paths(rec_urls)
        return rec_urls, rec_titles, rec_image_paths

def main():
    rec_sys = UCBRecSys()
    
    urls, _, _ = rec_sys.sample_urls(10)
    print(urls)

    # sample some urls
    urls = ['https://omnivorescookbook.com/chinese-egg-rolls/',
           'https://glebekitchen.com/miso-ramen-with-chashu-pork/',
           'https://omnivorescookbook.com/pineapple-buns/',
           'https://omnivorescookbook.com/easy-swiss-chard-stir-fry/',
           'https://thewoksoflife.com/stuffed-chicken-breast-sticky-rice/',
           'https://glebekitchen.com/spicy-miso-grilled-chicken/',
           'https://thewoksoflife.com/shrimp-lo-mein/',
           'https://thewoksoflife.com/stir-fried-cabbage-glass-noodles/',
           'https://glebekitchen.com/indian-restaurant-madras-curry/',
           'https://thewoksoflife.com/honey-sriracha-roasted-brussels-sprouts/']

    rec_urls, rec_titles, rec_image_paths = rec_sys.get_recs(urls)
    rec_sys.plot_images(rec_image_paths)
    
    for a, b in zip(rec_urls, rec_titles):
        print(a, b)

if __name__ == "__main__":
    main()