# recipe_rex

Project for CS329s: Machine Learning System Design

https://stanford-cs329s.github.io/reports/tender-recipe-recommendations/

## Download Requirements

Run `pip install -r requirements.txt` to install python dependencies

## Scrape recipes from webiste

Raw data is scraped by running the `scrape_recipes.ipynb` notebook in order to scrape Asian websites for around 5 websites

## Saving Features and Data

0. `cd feature_generation`

1. Run `python save_recipes.py` in order to save the `clean_data/all_recipes_nutrient.csv` and `clean_data/url_index_mapping.csv` csv files

2. Run `python save_images.py` in order save the image files from the scraped websites locally to the `images` directory. 

3. Run `python center_crop_resize_images.py` in order to resize and center crop all images to 200 by 200 to the `images_resized` directory so that thumbnails are all standardized

4. Run `python get_embeddings.py` in order to save the embeddings needed to run recommendation algorithms. This saves 4 files: `clean_data/{folder}/nutrient_features.csv`, `clean_data/{folder}ing_features.csv`,  `clean_data/{folder}embeddings_features_mvp.csv`, and `clean_data/embeddings_mvp_scaled.csv`, where the embeddings scaled is used for recipe similarity and the other csv's are intermediate. 

-- Folder represents ['mains', 'desserts', 'sides']

5. Run `python label_recipes.py` to get the keyword labels for our recipes

## Serving Recommendations

1. `serve_recs.py` contains relevant API class for grabbing urls and images in order to serve and sample recipes for application

2. `streamlit run ucb_rex.py` for ucb algorithm app locally
