import pandas as pd
import matplotlib.pyplot as plt
import math
import random

from get_recommendations_knn import get_recs_knn_average
from matplotlib import image 
from collections import defaultdict, Counter

class UCBRecSys():
    
    def __init__(self, folder = 'mains', file = 'mains_filter'):
        # load embeddings and index map
        self.embeddings_df_scaled = pd.read_csv(f'clean_data/{folder}/embeddings_{file}_scaled.csv', index_col = 'url')
        self.url_index_mapping = pd.read_csv(f'clean_data/{folder}/{file}_url_index_mapping.csv', index_col = 'url')    

        self.meat_labels = pd.read_csv(f'clean_data/{folder}/meat_labels.csv', index_col = 'url').loc[self.embeddings_df_scaled.index]
        self.starch_labels = pd.read_csv(f'clean_data/{folder}/starch_labels.csv', index_col = 'url').loc[self.embeddings_df_scaled.index]
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

        # set of currently served urls
        self.urls = set()

    def get_labels(self, urls):
        return [self.all_labels[axis].loc[urls] for axis in self.axes]

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
        # help print out what the current ucb selections are
        print(sorted(ucb_values.items(), key = lambda x: -x[1]))

        # return arm with largest ucb
        max_ = max(ucb_values.values())
        for key in ucb_values:
            if ucb_values[key] == max_:
                return key

    # update our arms
    def update_counts(self, url, increment = 1):
        # add or remove to url set
        if increment > 0:
            self.urls.add(url)
        else:
            self.urls.remove(url)

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

        filtered_urls = None
        for axis in self.axes:
            label_df = self.all_labels[axis]
            key = key_dict[axis]
            key_urls = set(label_df[label_df[key] == 1].index) - self.urls
            if filtered_urls is None:
                filtered_urls = key_urls
            else:
                filtered_urls &= key_urls 

        # sample a random url from this selected list
        if len(filtered_urls) > 1:
            print(f'key dict is {key_dict}')
            return random.choice(list(filtered_urls))
        else:
            axis = random.choice(self.axes)
            label_df = self.all_labels[axis]
            key = key_dict[axis]
            key_urls = set(label_df[label_df[key] == 1].index) - self.urls
            print('axis is {}, key is {}'.format(axis, key))
            return random.choice(list(key_urls))

    # sample url by generating key_dict either randomly or through ucb
    def sample_url(self, is_not_eval, rand = False):
        key_dict = {}
        for axis in self.axes:
            if rand:
                key = random.choice(self.all_labels[axis].columns)
            else:
                key = self.select_axis_arm(axis)
            key_dict[axis] = key

        url = self.get_random_url(key_dict)
        if is_not_eval:
            self.update_counts(url)
        else:
            self.urls.add(url)

        return url

    # randomly sample some urls and image paths
    def sample_urls(self, num_samples = 4, num_random = 1, is_not_eval = True):
        urls = []

        # select how many random and how many greedy
        num_greedy = num_samples - num_random

        # select random keys and then get random url
        for _ in range(num_random):
            url = self.sample_url(is_not_eval, rand = True)
            urls.append(url)

        # select random urls based on meats based on ucb, update with reward 1
        for _ in range(num_greedy):
            url = self.sample_url(is_not_eval, rand = False)
            urls.append(url)

        # random.shuffle(urls)

        titles = self.url_index_mapping.loc[urls]['title'].values
        total_time = self.url_index_mapping.loc[urls]['total_time'].values
        num_ingredients = self.url_index_mapping.loc[urls]['num_ingredients'].values
        image_paths = self.get_image_paths(urls)
        
        return urls, titles, image_paths, total_time, num_ingredients
    
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

    def unwrap_tuple(self, tup):
        d = {}
        for i, axis in enumerate(self.axes):
            d[axis] = [tup[i]]
        return d

    def string_dict(self, d):
        l = []
        for axis in self.axes:
            l.append(d[axis][0])
        return ' '.join(l)

    def get_most_common_labels(self, urls, cutoff = 3):
        import itertools

        self.label_counts = Counter()
        for url in urls:
            axis_keys = []
            for axis in self.axes:
                label_df = self.all_labels[axis] 
                keys = [key for key, val in label_df.loc[url].items() if val == 1]
                axis_keys.append(keys)

            for tup in itertools.product(*axis_keys):
                self.label_counts[tup] += 1
        print(self.label_counts)
        
        most_common_labels = self.label_counts.most_common(4)
        return [self.unwrap_tuple(tup) for tup, count in most_common_labels if count >= cutoff]

    def get_recs_filter(self, urls, all_filters, excluded_urls = set(), num_recs = 10):
        filtered_urls = None
        for axis in self.axes:
            filters = all_filters[axis]
            filtered_urls_axis = set()
            label_df = self.all_labels[axis]

            # if at least 1 filter, then find the relevant keys if len(filters) > 0: # union all relevant keys
            if len(filters) > 0:
                for key in filters:
                    filtered_urls_axis |= set(label_df[label_df[key] == 1].index)
            else:
                filtered_urls_axis = set(label_df.index)

            # intersect the axes
            if filtered_urls is None:
                filtered_urls = filtered_urls_axis
            else:
                filtered_urls &= filtered_urls_axis

        # restrict to urls in embeddings df
        filtered_urls &= set(self.embeddings_df_scaled.index)
        filtered_urls -= excluded_urls

        _, rec_urls = get_recs_knn_average(self.embeddings_df_scaled, urls, filtered_urls, num_recs)
        rec_titles = self.url_index_mapping.loc[rec_urls]['title'].values
        rec_image_paths = self.get_image_paths(rec_urls)

        return rec_urls, rec_titles, rec_image_paths

    # return a dictionary mapping top 10 urls and title and image index
    def get_recs(self, urls, value_cutoff = 0.6):
        # get filter based on selection criterion, and then find nearest neighbors
        all_filters = {}

        for axis in self.axes:  
            conf_df = self.get_value_df(axis)
            # pick the ones with the value cutoff
            filters = conf_df[conf_df >= value_cutoff].index
            all_filters[axis] = filters

        print(all_filters)
        return self.get_recs_filter(urls, all_filters)

    def get_recs_most_common(self, urls):
        d = {}
        all_filters_list = self.get_most_common_labels(urls)
        excluded_url_list = []
        for all_filters in all_filters_list:
            rec_urls, rec_titles, rec_image_paths = self.get_recs_filter(urls, all_filters, excluded_urls = set(excluded_url_list), num_recs = 5)
            excluded_url_list += list(rec_urls)
            d[self.string_dict(all_filters)] = (rec_urls, rec_titles, rec_image_paths)
        return d

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