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

import sys
sys.path.append('../')
from serve_recs import *

debug = False

# method to get 4 random images
def get_images(rec_sys, idx):
    return rec_sys.sample_urls(4)
      
# method to reset the selections on reset
def reset_choice(state):
    if state.index < state.num_pages:
        state.url_selections[state.index] = -1
        state.title_selections[state.index] = -1
        state.image_selections[state.index] = -1

def top_bar(state):
    b, r, f = st.beta_columns(3)
    with b:
        if st.button('Back') and state.index > 0:
            state.index = state.index - 1
    with r:
        if st.button('Refresh'):
            reset_choice(state)
            state.all_params[state.index] = get_images(state.rec_sys, state.index)
    with f:
        if st.button('Forward') and state.index < state.num_pages:
            # proceed if we made a selection
            if state.title_selections[state.index] != -1:
                state.index = state.index + 1
            else:
                error_message = "Please make a selection"

# initialize placeholders for buttons / titles
def init_placeholders(state):
    # place holders for progress bar and page number
    state.header = st.empty()
    state.progress_bar = st.empty()
    state.error_message = st.empty()
    state.buttons = [] 
    state.cols = st.beta_columns(4)
    for i in range(4):
        with state.cols[i]:
            state.buttons.append(st.empty())

def selection_buttons(state):
    error_message = ""

    # create columns if second to last page 
    state.sel = -1

    for i in range(4):
        with state.cols[i]:
            if state.buttons[i].button('Recipe {}'.format(i)) and state.index < state.num_pages:
                state.index += 1
                state.sel = i

    # set header and message
    if state.index < state.num_pages:            
        state.error_message.write(error_message)
        state.header.header(f'Page {state.index+1}: Which do you prefer?')

# render all the starting buttons
def render_buttons(state):
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
        params = state.all_params[state.index-1]
        urls, titles, pics = params
        state.url_selections[prev_index] = urls[state.sel]
        state.title_selections[prev_index] = titles[state.sel].capitalize()
        state.image_selections[prev_index] = pics[state.sel]

# choice screen image rendering 
def display_choices(state):
    params = state.all_params[state.index]
    urls = params[0]
    titles = params[1]
    pics = params[2]

    for i in range(4):
        with state.cols[i]:
            # state.buttons[i].button('test')
            st.image([pics[i]], use_column_width=True)
            st.write("{}".format(titles[i].capitalize()))

# result screen image rendering
def display_results(state):
    state.header.header('Final Recommendations')

    # reset state buttons
    if state.buttons:
        for i in range(4):
            state.buttons[i].empty()
    
    # 2 columns for 10 recs 
    row1 = st.beta_columns(5)
    row2 = st.beta_columns(5)
    
    # INSERT rec sys 
    rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(state.url_selections)

    for i in range(5):
        with row1[i]:
            st.image([rec_image_paths[i]], use_column_width=True)
            st.write(f"[{rec_titles[i]}]({rec_urls[i]})")
        with row2[i]:
            st.image([rec_image_paths[5+i]], use_column_width=True)
            st.write(f"[{rec_titles[5+i]}]({rec_urls[5+i]})")
    
    # also insert user choices 
    st.header('Your Choices')
    row3 = st.beta_columns(state.num_pages)
    
    for i in range(state.num_pages):
        with row3[i]:
            st.image([state.image_selections[i]], use_column_width=True)
            st.write(f"[{state.title_selections[i]}]({state.url_selections[i]})")

# render the images
def render_images(state, debug = debug):
    # handle the previous click
    update_selections(state)

    # (5) random choice screen vs, result screen
    if state.index < state.num_pages:
        display_choices(state)
    else:
        display_results(state)

    if debug:
        st.write(state.rec_sys.urls)
        st.write(f"index: {state.index}")
        st.write(f"selection: {state.sel}")
        st.write(state.title_selections)

def render():
    num_pages = 5
    rec_sys = KNNRecSys('desserts', 'desserts_filter')
    # rec_sys = KNNRecSys('sides', 'sides_filter')
    state = ss.get(rec_sys = rec_sys,
                 all_params = {idx: get_images(rec_sys, idx) for idx in range(num_pages)},
                 index = 0, 
                 url_selections = [-1 for _ in range(num_pages)],
                 title_selections = [-1 for _ in range(num_pages)],
                 image_selections = [-1 for _ in range(num_pages)],
                 num_pages = num_pages,
                 sel = -1,
                 cols = None
                )
    
    render_buttons(state)
    render_images(state)

render()