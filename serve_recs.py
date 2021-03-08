import pandas as pd
import matplotlib.pyplot as plt

from get_recommendations_knn import get_recs_knn_average
from matplotlib import image 

class KNNRecSys():
    def __init__(self, folder, file):
        # load embeddings and index map
        self.embeddings_df_scaled = pd.read_csv(f'clean_data/{folder}/embeddings_{file}_scaled.csv', index_col = 'url')
        self.url_index_mapping = pd.read_csv(f'clean_data/{folder}/{file}_url_index_mapping.csv', index_col = 'url')    

    # randomly sample some urls and image paths
    def sample_urls(self, samples = 4):
        urls = self.embeddings_df_scaled.sample(samples).index
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
        _, rec_urls = get_recs_knn_average(self.embeddings_df_scaled, urls)
        rec_titles = self.url_index_mapping.loc[rec_urls]['title'].values
        rec_image_paths = self.get_image_paths(rec_urls)
        return rec_urls, rec_titles, rec_image_paths

def main():
    rec_sys = KNNRecSys()
    
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