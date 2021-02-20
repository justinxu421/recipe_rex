# recipe_rex

## Download Requirements

Run `pip install -r requirements.txt` to install python dependencies

## Saving Features and Data

0. Raw data is scraped by running the `scrape_recipes.ipynb` notebook in order to scrape Asian websites for ~5 websites

1. Run `python save_recipes.py` in order to save the `clean_data/all_recipes_nutrient.csv` and `clean_data/url_index_mapping.csv` csv files

2. Run `python save_images.py` in order save the image files from the scraped websites locally to the `images` directory. 

3. Run `python center_crop_resize_images.py` in order to resize and center crop all images to 200 by 200 to the `images_resized` directory so that thumbnails are all standardized

4. Run `python get_embeddings.py` in order to save the embeddings needed to run recommendation algorithms. This saves 4 files: `clean_data/nutrient_features.csv`, `clean_data/ing_features.csv`,  `clean_data/embeddings_features_mvp.csv`, and `clean_data/embeddings_mvp_scaled.csv`, where the embeddings scaled is used for recipe similarity and the other csv's are intermediate

## Serving Recommendations

1. `serve_recs.py` contains relevant API class for grabbing urls and images in order to serve and sample recipes for application