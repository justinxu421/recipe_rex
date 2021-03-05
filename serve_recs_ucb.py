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
        self.embeddings_df_scaled = pd.read_csv('clean_data/mains/embeddings_main_filter_scaled.csv', index_col = 'url')
        self.url_index_mapping = pd.read_csv('clean_data/mains/mains_url_index_mapping.csv', index_col = 'url')    
        self.meat_labels = pd.read_csv('clean_data/mains/meat_labels.csv', index_col = 'url')
        # self.starch_labels = pd.read_csv('../clean_data/mains/starch_labels.csv', index_col = 'url')
        # self.taste_labels = pd.read_csv('../clean_data/mains/nutrient_features.csv', index_col = 'url')

        self.meats = self.meat_labels.columns
        # self.starches = self.starch_labels.columns
        # self.tastes = self.taste_labels.columns

        # just set it to meats
        # self.all_labels = self.taste_labels.join(self.starch_labels).join(self.meat_labels).dropna()
        self.all_labels = self.meat_labels.loc[self.embeddings_df_scaled.index]

        # initialize ucb parameters
        self.counts = {meat: 0 for meat in self.meats}
        self.totals = {meat: 0 for meat in self.meats}

    # get lower and upper confidence bounds
    def get_confidence_bounds(self):
        bounds = {}
        total_counts = sum(self.counts.values())
        for meat in self.meats:
            # offset is calculated to figure out UCB
            offset = 0 if self.counts[meat] == 0 else math.sqrt((2 * math.log(total_counts)) / self.counts[meat]) 
            value = 0 if self.counts[meat] == 0 else self.totals[meat] / self.counts[meat]
            lower, upper = value - offset, value + offset
            bounds[meat] = (lower, upper)

        return bounds

    # get the value
    def get_confidence_df(self):
        bounds = self.get_confidence_bounds() 
        conf_df = pd.DataFrame(bounds).T
        conf_df.columns = ['lower', 'upper']
        conf_df['val'] = (conf_df['lower'] + conf_df['upper']) / 2
        return conf_df['val']

    # select arm based on UCB criterion
    def select_meat_arm(self):
        # make a selection if never selected
        for meat in self.meats:
            if self.counts[meat] == 0:
                return meat

        ucb_values = {meat: bound[1] for meat, bound in self.get_confidence_bounds().items()}

        # return arm with largest ucb
        max_ = max(ucb_values.values())
        for meat in ucb_values:
            if ucb_values[meat] == max_:
                return meat 

    # update our arms
    def update_meat_counts(self, url, increment = 1):
        for meat, val in self.meat_labels.loc[url].items():
            if val == 1:
                self.counts[meat] += increment

    # update totals after selection is made
    def update_meat_values(self, url, choices, reward = 1):
        choice_counts = defaultdict(int)
        for url_ in choices:
            for meat, val in self.meat_labels.loc[url_].items():
                if val == 1:
                    choice_counts[meat] += reward

        for meat, val in self.meat_labels.loc[url].items():
            if val == 1:
                self.totals[meat] += choice_counts[meat]

    # based on the selected meat arm, pick a random url
    def get_random_url_meat(self, meat):
        meat_df = self.meat_labels[self.meat_labels[meat] == 1]
        return meat_df.sample(1).index.values[0]

    # randomly sample some urls and image paths
    def sample_urls(self, num_samples = 4, random_chance = 0.25):
        meats = []
        urls = []

        num_random = int(random_chance * num_samples)
        num_greedy = num_samples - num_random

        # select random meat and random url
        for _ in range(num_random):
            meat = random.choice(self.meats)
            meats.append(meat)

            url = self.get_random_url_meat(meat)
            self.update_meat_counts(url)
            urls.append(url)

        # select random urls based on meats based on ucb, update with reward 1
        for _ in range(num_greedy):
            meat = self.select_meat_arm()
            meats.append(meat)

            url = self.get_random_url_meat(meat)
            self.update_meat_counts(url)
            urls.append(url)

        print(meats)

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
    def get_recs(self, urls):
        conf_df = self.get_confidence_df()

        # get filter based on selection criterion, and then find nearest neighbors
        filtered_urls = set()
        filters = conf_df[conf_df >= 0.4].index
        print(filters)
        for meat in filters:
            filtered_urls |= set(self.meat_labels[self.meat_labels[meat] == 1].index)
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