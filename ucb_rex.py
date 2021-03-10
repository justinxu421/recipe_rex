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

debug = False

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
        if st.button('Forward') and state.index < state.num_pages:
            # proceed if we made a selection
            if state.selections[state.filter_sel][state.index] != (-1, -1, -1):
                state.index = state.index + 1
            else:
                state.msg = "Please make a selection"

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
    state.progress_bar.progress(state.index / state.num_pages)

# update the previous entry with selection
def update_selections(state):
    # -1 means dont do anything
    if state.sel >= 0:
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

            if debug:
                st.write(f"[{titles[i]}]({urls[i]})")
            else:
                st.write('{}'.format(titles[i]))


#             st.write(f'total time: {total_time[i]}')
#             st.write(f'num ingredients: {num_ingredients[i]}')

#             for key, val in meat_labels.iloc[i].items():
#                 if val == 1:
#                     st.text(key)

#             for key, val in starch_labels.iloc[i].items():
#                 if val == 1:
#                     st.text(key)
                    
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
    
    # INSERT rec sys 
    url_selections = [x[0] for x in state.selections[state.filter_sel]]


    d = state.rec_sys.get_recs_most_common(url_selections)
    if d:
        for title, (rec_urls, rec_titles, rec_image_paths) in d.items():
            # st.write(len(rec_urls))
            write_recs(title, rec_urls, rec_titles, rec_image_paths)
    else:
        ## Overall RECS
        rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(url_selections)
        write_recs('Your final recs', rec_urls, rec_titles, rec_image_paths)

    if debug:
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

# render the images
def render_images(state, debug = debug):
    # handle the previous click
    update_selections(state)

    # (num_pages) random choice screen vs, result screen
    if state.index < state.num_pages:
        display_choices(state)
    else:
        display_results(state)

    meat, starch = st.beta_columns(2)
    meat_vals = state.rec_sys.get_value_df('meat')
    starch_vals = state.rec_sys.get_value_df('starch')

    if state.index > 0:
        with meat: 
            meat_vals = meat_vals.reset_index().rename(columns = {'index': 'meat', 'val': 'score'})
            c = alt.Chart(meat_vals).mark_bar().encode(
                x = 'score:Q',
                y = 'meat:O',
                color = 'meat'
            # ).configure_mark(
            #     color = 'meat'
            ).properties(height=400
            ).configure_axis(
                labelFontSize=14,
                titleFontSize=14
            )
            st.altair_chart(c, use_container_width=True)
        with starch:
            starch_vals = starch_vals.reset_index().rename(columns = {'index': 'starch', 'val': 'score'})
            c = alt.Chart(starch_vals).mark_bar().encode(
                x = 'score:Q',
                y = 'starch:O',
                color = 'starch',
            # ).configure_mark(
            #     color = 'starch'
            ).properties(height=400
            ).configure_axis(
                labelFontSize=14,
                titleFontSize=14
            )
            st.altair_chart(c, use_container_width=True)

    if debug:
        st.write(f"index: {state.index}")
        st.write(f"selection: {state.sel}")
        st.write(state.rec_sys.urls)

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
            <div class="card-header" id="headingOne">
              <h5 class="mb-0">
                <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                More Info
                </button>
              </h5>
            </div>
            <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
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
    
    
def render_legend():
    emoji_index = 1
    components.html(
        f"""
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

        <div id="accordion">
          <div class="card">
            <div class="card-header" id="headingOne">
              <h5 class="mb-0">
                <button class="btn btn-link" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                Emoji Legend
                </button>
              </h5>
            </div>
            <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordion">
              <div class="card-body">
               <b> {cook_time_emoji}: </b> cook time <br /> 
                <b> {meat_tag_dict['poultry'][emoji_index]}: </b> poultry<br /> 
                <b> {meat_tag_dict['pork'][emoji_index]}: </b> pork <br />
                <b> {meat_tag_dict['beef'][emoji_index]}: </b> beef <br /> 
                <b>{meat_tag_dict['fish'][emoji_index]}: </b> fish <br /> 
                <b>{meat_tag_dict['seafood'][emoji_index]}: </b> seafood <br /> 
                <b>{meat_tag_dict['veg'][emoji_index]}: </b> vegetarian <br /> 
                <b>{starch_tag_dict['noodle'][emoji_index]}: </b> noodle <br /> 
                <b>{starch_tag_dict['rice'][emoji_index]}: </b> rice <br /> 
                <b>{starch_tag_dict['soup'][emoji_index]}: </b> soup <br /> 
                <b>{starch_tag_dict['stew'][emoji_index]}: </b> stew <br /> 
              </div>
            </div>
          </div>
        </div>
        """,
        height=1000,
        scrolling=True
    )
    

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

    state.filter_index[state.filter_sel] = state.index
    state.filter_sel = st.sidebar.radio('Filter selection', filters)
    state.index = state.filter_index[state.filter_sel]
    state.rec_sys = state.rec_sys_dict[state.filter_sel]

    render_buttons(state)
    render_images(state)
    render_legend()

render()
