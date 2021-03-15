#!/usr/bin/env python
# coding: utf-8
import stream.SessionState as ss
import socket

# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import random
import streamlit as st
import altair as alt
import streamlit.components.v1 as components
from annotated_text import annotated_text, annotation

import sys
sys.path.append('../')
from serve_recs_ucb import *
from serve_recs import *

# values = ['color' (if wanted to highlight), 'emoji']
meat_tag_dict = {
    'poultry':['#8ef', '🍗'],
    'beef':['#faa', '🥩'],
    'pork':['#afa', '🐖'],
    'fish':['#fea', '🐟'],
    'seafood':['#8ef', '🦐'],
    'veg':['#ff0', '🥕'],
}

starch_tag_dict = {
    'noodle':['#8ef', '🍜'],
    'rice':['#afa', '🍚'],
    'soup':['#ff0', '🥣'],
    'stew':['#fe0', '🍲'],
    'none':['#fa0', ''],
}

cook_time_emoji = '⏱️'

# method to get 4 random images
def get_images(rec_sys, idx):
    return rec_sys.sample_urls(4)
      
# method to reset the selections on reset
def reset_choice(state):
    if state.index < state.num_pages:
        # reset counts on refresh
        for url in state.all_params[state.filter_sel][state.index][0]:
            state.rec_sys.update_counts(url, -1)

        # reset selections
        state.selections[state.filter_sel][state.index] = (-1, -1, -1)

def top_bar(state):
    b, r, f = st.beta_columns(3)
    with b:
        if st.button('Back') and state.index > 0:
            state.index = state.index - 1
    with r:
        if st.button('Refresh'):
            if state.index < state.num_pages:
                reset_choice(state)
                state.all_params[state.filter_sel][state.index] = get_images(state.rec_sys, state.index)
    with f:
        if st.button('Forward'):
            if state.index <= state.num_pages-1: 
                # we're in the explore stage
                if state.selections[state.filter_sel][state.index] != (-1, -1, -1):
                    # proceed if we made a selection
                    state.index = state.index + 1
                else:
                    # give helpful error message
                    state.msg = "Please make a selection"
            elif state.index == state.num_pages:
                # we're in the eval stage
                num_selections = np.sum(state.eval_selected_grid)
                num_diff = num_selections - state.eval_num_recs
                if num_diff < 0: 
                    state.msg = f"You selected {int(-num_diff)} too few! Please choose more."
                elif num_diff > 0:
                    state.msg = f"You selected {int(num_diff)} too many! Please choose less."
                else:
                    state.index = state.index + 1

# initialize placeholders for buttons / titles
def init_placeholders(state):
    # place holders for progress bar and page number
    state.header = st.empty()
    state.progress_bar = st.empty()
    state.error_message = st.empty()
    state.buttons = [] 
    num_cols = 4
    state.cols = st.beta_columns(num_cols)
    for i in range(num_cols):
        with state.cols[i]:
            state.buttons.append(st.empty())
        
def selection_buttons(state):
    # create columns if second to last page 
    state.sel = -1

    for i in range(4):
        with state.cols[i]:
            if state.buttons[i].button('Recipe {}'.format(i)) and state.index < state.num_pages:
                state.index += 1
                state.sel = i

    # set header and message
    if state.index < state.num_pages:            
        state.error_message.write(state.msg)
        state.header.header(f'Page {state.index+1}: Which do you prefer?')

# render all the starting buttons
def render_buttons(state):
    state.msg = ""

    # render separate buttons
    top_bar(state)
    init_placeholders(state) 

    # choice screens
    if state.index < state.num_pages:            
        selection_buttons(state)

    # set progress bar
    state.progress_bar.progress(state.index / (state.num_pages+1))

# update the previous entry with selection
def update_selections(state):
    # -1 means dont do anything
    if state.sel >= 0 and state.index <= state.num_pages:
        prev_index = state.index - 1
        params = state.all_params[state.filter_sel][state.index-1]

        urls = params[0]
        titles = params[1]
        pics = params[2]

        # we also need to upate state if we have previously selected
        prev_url_sel = state.selections[state.filter_sel][prev_index][0]
        if prev_url_sel != -1:
            state.rec_sys.update_values(prev_url_sel, urls, -1)

        # write selections
        state.selections[state.filter_sel][prev_index] = (urls[state.sel], titles[state.sel], pics[state.sel])

        # update rewards
        state.rec_sys.update_values(urls[state.sel], urls)

# choice screen image rendering 
def display_choices(state):
    # generate images if not already present
    if state.all_params[state.filter_sel][state.index] == -1:
        state.all_params[state.filter_sel][state.index] = get_images(state.rec_sys, state.index)

    params = state.all_params[state.filter_sel][state.index]
    urls = params[0]
    titles = params[1]
    pics = params[2]
    total_time = params[3]
    num_ingredients = params[4]

    meat_labels = state.rec_sys.get_labels(state.all_params[state.filter_sel][state.index][0])[0]
    starch_labels = state.rec_sys.get_labels(state.all_params[state.filter_sel][state.index][0])[1]

    meat_labels_dict = {}
    starch_labels_dict = {}
    for i in range(4):
        with state.cols[i]:
            # state.buttons[i].button('test')
            st.image([pics[i]], use_column_width=True)

            if state.debug:
                st.write(f"[{titles[i]}]({urls[i]})")
            else:
                st.write('{}'.format(titles[i]))
                    
            meat_labels_included = []
            starch_labels_included = []
            
            for key, val in meat_labels.iloc[i].items():
                if val == 1:
                    meat_labels_included.append(str(key))

            for key, val in starch_labels.iloc[i].items():
                if val == 1:
                    starch_labels_included.append(str(key))

            meat_labels_dict[i] = meat_labels_included
            starch_labels_dict[i] = starch_labels_included
    
    bio = st.beta_columns(4) 
    for i in range(4):
        with bio[i]:
            display_bio(total_time[i], meat_labels_dict[i], starch_labels_dict[i], num_ingredients[i])

def write_recs(title, rec_urls, rec_titles, rec_image_paths):
    st.subheader(title)

    
    # 2 columns for 10 recs 
    row1 = st.beta_columns(5)
    row2 = st.beta_columns(5)
    
    for i in range(5):
        with row1[i]:
            if i < len(rec_urls):
                st.image([rec_image_paths[i]], use_column_width=True)
                st.write(f"[{rec_titles[i]}]({rec_urls[i]})")
        with row2[i]:
            if 5+i < len(rec_urls):
                st.image([rec_image_paths[5+i]], use_column_width=True)
                st.write(f"[{rec_titles[5+i]}]({rec_urls[5+i]})")

# result screen image rendering
def display_results(state):
    state.header.header('Recipes you might like')

    # reset state buttons
    if state.buttons:
        for i in range(4):
            state.buttons[i].empty()

    st.markdown(f'During evaluation, you chose **{state.eval_percent_recs_chosen * 100:.0f}%** of these (Please fill out on Google Form).')
    
    # INSERT rec sys 
    url_selections = [x[0] for x in state.selections[state.filter_sel]]

    d = state.rec_sys.get_recs_most_common(url_selections)
    if state.filter_sel == 'mains' and d:
        for title, (rec_urls, rec_titles, rec_image_paths) in d.items():
            # st.write(len(rec_urls))
            write_recs(title, rec_urls, rec_titles, rec_image_paths)
    else:
        ## Overall RECS
        rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(url_selections)
        write_recs('Your final recs', rec_urls, rec_titles, rec_image_paths)

    if state.debug:
        st.write({' '.join(a): b for a, b in state.rec_sys.label_counts.items()})
    
    # also insert user choices 
    st.header('Your Choices')

    if state.num_pages > 5:
        half = state.num_pages // 2
        row3 = st.beta_columns(half)
        row4 = st.beta_columns(state.num_pages - half)
        
        for i in range(half):
            url, title, image_path = state.selections[state.filter_sel][i]
            with row3[i]:
                st.image([image_path], use_column_width=True)
                st.write(f"[{title}]({url})")

        for i in range(state.num_pages - half):
            url, title, image_path = state.selections[state.filter_sel][5+i]
            with row4[i]:
                st.image([image_path], use_column_width=True)
                st.write(f"[{title}]({url})")
    else:      
        row3 = st.beta_columns(state.num_pages)
        
        for i in range(state.num_pages):
            url, title, image_path = state.selections[state.filter_sel][i]
            with row3[i]:
                st.image([image_path], use_column_width=True)
                st.write(f"[{title}]({url})")

# Shows evaluation page before results
def display_evaluation(state):
    # TODO: currently, the recommendations stay static even after going backwards and 
    # selecting something new
    
    # reset state buttons
    if state.buttons:
        for i in range(4):
            state.buttons[i].empty()

    # important to store to state, so it doesn't change every page refresh
    if not hasattr(state, "eval_recipes_grid"):

        # Get the rec'd recipes
        url_selections = [x[0] for x in state.selections[state.filter_sel]]
        state.recs_list = []

        d = state.rec_sys.get_recs_most_common(url_selections)
        if state.filter_sel == 'mains' and d:        
            # KNN within UCB selected meat-starch categories
            for _, (rec_urls, rec_titles, rec_image_paths) in d.items():
                state.recs_list.extend(list(zip(rec_urls, rec_titles, rec_image_paths)))

            # fallback behavior
            if len(state.recs_list) == 0:
                # KNN over entire dataset
                rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(url_selections)

        else:
            # KNN over entire dataset
            rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(url_selections)
            state.recs_list.extend(list(zip(rec_urls, rec_titles, rec_image_paths)))
        
        # add to the url set so we don't have repeats surface 
        for url, _ ,_ in state.recs_list:
            state.rec_sys.urls.add(url)

        state.eval_num_recs = len(state.recs_list)
        
        # Get the random recipes
        num_randoms = len(state.recs_list)
        rand_urls, rand_titles, rand_image_paths, _, _ = state.rec_sys.sample_urls(
            num_samples=num_randoms,
            num_random=num_randoms,
            is_not_eval=False
        ) 
        state.eval_random_recipes = list(zip(rand_urls, rand_titles, rand_image_paths))

        # Shuffle recommendations and randoms, then assign each into a recipe grid
        # Tuple format: [is_rec, url, title, path], is_rec = 0/1 (false, true)
        state.eval_recipes_grid = [(1, *rec) for rec in state.recs_list] + [(0, *rand) for rand in state.eval_random_recipes]
        random.shuffle(state.eval_recipes_grid)

        num_cols = 5 # FIXME hardcoded default num columns
        num_rows = (len(state.eval_recipes_grid) - 1) // num_cols + 1
        
        # Create selections grid
        state.eval_selected_grid = [[0 for _ in range(num_cols)] for _ in range(num_rows)] 
    else:
        num_rows, num_cols = len(state.eval_selected_grid), len(state.eval_selected_grid[0])
    
    state.header.header(f'Evaluate us by choosing your top {state.eval_num_recs} recipes')
    state.error_message.write(state.msg)
    
    # Create streamlit display grid
    st_grid = [st.beta_columns(num_cols) for _ in range(num_rows)]
    
    if state.debug:
        st.write(len(state.rec_sys.urls))
        st.write([x[1] for x in state.eval_random_recipes])
        st.write([x[1] for x in state.recs_list])
        st.write(state.eval_recipes_grid)
    
    # Display grid of recipes with checkboxes
    for i in range(num_rows):
        for j in range(num_cols):
            if 5*i + j < len(state.eval_recipes_grid):
                _, _, title, image_path = state.eval_recipes_grid[5*i + j]
            
                with st_grid[i][j]:
                    st.image([image_path], use_column_width=True)
                    curr_selection = state.eval_selected_grid[i][j] # ensures checkbox stays check if go back then forward to this page
                    state.eval_selected_grid[i][j] = st.checkbox(title, curr_selection)
    
    # Get % recommendations chosen and save in state
    select_idxs = []
    for i in range(num_rows): 
        for j in range(num_cols):
            if state.eval_selected_grid[i][j]:
                select_idxs.append(5*i + j)

    selections = [x for idx, x  in enumerate(state.eval_recipes_grid) if idx in select_idxs]
    state.eval_percent_recs_chosen = np.mean([int(is_rec) for is_rec, _, _, _ in selections])
    # state.eval_percent_recs_chosen = np.mean([int(is_rec) for idx, (is_rec, _, _, _) in enumerate(state.eval_recipes_grid) if idx in select_idxs])
    
    # Save urls chosen in state, for future use e.g. highlighting in the results page
    # or using to refine the results page
    state.eval_selected_urls = [url for _, url, _, _ in selections]
    
    if state.debug:
        # st.write(f"{int(state.eval_percent_recs_chosen * len(selections))} of {len(selections)} choices are recs")
        st.write("Selection grid:")
        st.write(state.eval_selected_grid)

    
# render the images
def render_images(state):
    # handle the previous click
    update_selections(state)
    
    # Show explore screen, evaluate screen, or results screens
    if state.index <= state.num_pages-1:
        display_choices(state)
    elif state.index == state.num_pages:
        display_evaluation(state)
    else:
        # FIXME: currently, we have num_pages+1. cannot increment num_pages variable,
        # since a couple other places rely on num_pages for initializing selections made.
        # Current hack is to use num_pages+1 in progess bar as well.
        display_results(state)

    meat, starch = st.beta_columns(2)
    meat_vals = state.rec_sys.get_value_df('meat')
    starch_vals = state.rec_sys.get_value_df('starch')

    if state.index > 0:
        if state.filter_sel == 'mains' and state.index != state.num_pages:
            with meat: 
                meat_vals = meat_vals.reset_index().rename(columns = {'index': 'meat', 'val': 'score'})
                c = alt.Chart(meat_vals).mark_bar().encode(
                    x = 'score:Q',
                    y = 'meat:O',
                    color = alt.Color('meat', legend = None)
                ).properties(height=400
                ).configure_axis(
                    labelFontSize=12,
                    titleFontSize=14
                )
                st.altair_chart(c, use_container_width=True)
            with starch:
                starch_vals = starch_vals.reset_index().rename(columns = {'index': 'starch', 'val': 'score'})
                c = alt.Chart(starch_vals).mark_bar().encode(
                    x = 'score:Q',
                    y = 'starch:O',
                    color = alt.Color('starch', legend = None)
                ).properties(height=400
                ).configure_axis(
                    labelFontSize=12,
                    titleFontSize=14
                )
                st.altair_chart(c, use_container_width=True)

    if state.debug:
        st.write(f"index: {state.index}")
        st.write(f"selection: {state.sel}")
        st.write(f"number of urls in set: {len(state.rec_sys.urls)}")

        st.write(state.rec_sys.get_confidence_bounds('meat'))
        st.write(state.rec_sys.get_confidence_bounds('starch'))
        if state.index < state.num_pages:
            meat_labels = state.rec_sys.get_labels(state.all_params[state.filter_sel][state.index][0])[0]
            starch_labels = state.rec_sys.get_labels(state.all_params[state.filter_sel][state.index][0])[1]
            st.write(meat_labels)
            st.write(starch_labels)

        col1, col2 = st.beta_columns(2)
        with col1:
            st.write(meat_vals)
            st.write('counts')
            st.write(state.rec_sys.counts)
        with col2:
            st.write(starch_vals)
            st.write('totals')
            st.write(state.rec_sys.totals)
        st.write(state.selections[state.filter_sel])
        
def get_labels_as_tags(labels, dictionary, index_of_value, is_annotate, label_category = "none"):
    tags_string = ""
    
    for label in labels:
        if (is_annotate):
            tags_string += str(annotation(label, label_category, background=(dictionary[label])[index_of_value]))
        else:
            tags_string += str((dictionary[label])[index_of_value])
    
    return tags_string
        
# https://github.com/tvst/st-annotated-text
# https://docs.streamlit.io/en/stable/develop_streamlit_components.html
def display_bio(total_time, meat_labels, starch_labels, num_ingredients):        
    
    tags_string = ""
    tags_string += get_labels_as_tags(meat_labels, meat_tag_dict, 1, False)
    tags_string += get_labels_as_tags(starch_labels, starch_tag_dict, 1, False)

    # display bio
    components.html(
        f"""
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

        <div id="accordion">
          <div class="card">
            <div class="card-header" id="headingTwo">
              <h5 class="mb-0">
                <button class="btn btn-link collapsed" data-toggle="collapse" data-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                More Info
                </button>
              </h5>
            </div>
            <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordion">
              <div class="card-body">
                <b>{cook_time_emoji}: </b> {total_time} min<br /> 
                <b> Ingredients: </b> {num_ingredients} <br />
                <b>Tags: </b> {tags_string} <br /> 
              </div>
            </div>
          </div>
        </div>
        """,
        height=220,
        scrolling=True
    )
    
def render_help_expander():
    with st.sidebar.beta_expander("Help"):
        st.markdown("""
                    ### 🥩🥕🍜 Welcome 🥩🥕🍜 
                    
                    We are your personal recommendation system! Here's how it works:
                    
                    1. Choose the "main", "dessert", or "side" category under "Filter selection"
                    1. Choose your favorite recipe by clicking one of the "Recipe" buttons.
                        1. See the "More Info" dropdown for a quick biography of the recipe!
                        1. Click "Refresh" if you don't see any recipes you ❤️ 
                    1. Repeat (you'll choose 10 recipes total)
                    1. You'll reach our "Recipes you might like" page with 10 of the recipes we thought you might like 😋
                    """
                   );
        
        emoji_index = 1
        st.markdown(f"""
                    ### Legend
                    
                    {cook_time_emoji} cook time
                    
                    {meat_tag_dict['poultry'][emoji_index]} poultry
                    
                    {meat_tag_dict['pork'][emoji_index]} pork 

                    {meat_tag_dict['beef'][emoji_index]} beef  
                    
                    {meat_tag_dict['fish'][emoji_index]} fish
                    
                    {meat_tag_dict['seafood'][emoji_index]} seafood 
                    
                    {meat_tag_dict['veg'][emoji_index]} vegetarian 
                    
                    {starch_tag_dict['noodle'][emoji_index]} noodle 
                    
                    {starch_tag_dict['rice'][emoji_index]} rice
                    
                    {starch_tag_dict['soup'][emoji_index]} soup
                    
                    {starch_tag_dict['stew'][emoji_index]} stew 
                    """)



def render():
    st.set_page_config(layout="centered")

    num_pages = 10

    # filters to use
    filters = ['mains', 'desserts', 'sides']
    rec_sys_main = UCBRecSys('mains', 'mains_filter')
    rec_sys_dessert = UCBRecSys('desserts', 'desserts_filter')
    rec_sys_sides = UCBRecSys('sides', 'sides_filter')

    rec_sys_dict = {
        'mains': rec_sys_main,
        'desserts': rec_sys_dessert,
        'sides': rec_sys_sides
    }

    state = ss.get(rec_sys = rec_sys_main, 
         rec_sys_dict = rec_sys_dict,
         filter_sel = 'mains',
         debug = False,
         all_params = {filter_: {idx: -1 for idx in range(num_pages)} for filter_ in filters},
         num_pages = num_pages,
         # index to indicate page number
         filter_index = {filter_: 0 for filter_ in filters},
         index = 0, 
         # url, title, image path
         selections = {filter_: [(-1, -1, -1) for _ in range(num_pages)] for filter_ in filters},
         sel = -1,
         cols = None
     )

    state.debug = st.sidebar.checkbox('debug', value = False)
    state.filter_index[state.filter_sel] = state.index
    state.filter_sel = st.sidebar.radio('Filter selection', filters)
    state.index = state.filter_index[state.filter_sel]
    state.rec_sys = state.rec_sys_dict[state.filter_sel]

    render_help_expander()
    render_buttons(state)
    render_images(state)

render()
