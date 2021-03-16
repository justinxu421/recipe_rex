import urllib.request
import pandas as pd

all_dfs_nutrient = pd.read_csv('../clean_data/all/all_recipes_nutrient.csv')

# create agent that opens from a browser
opener=urllib.request.build_opener()
opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

for index, image_url in all_dfs_nutrient[['index', 'image_url']].to_numpy():
    try:
        urllib.request.urlretrieve(image_url, f"../images/image_{index}.jpg")
    except:
        print(index, image_url)