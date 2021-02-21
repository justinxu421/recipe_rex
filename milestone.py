#!/usr/bin/env python
# coding: utf-8
from serve_recs import KNNRecSys
import SessionState
import socket

import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import random

def get_images(idx):
    rec_sys = KNNRecSys()
    return rec_sys.sample_urls(4)
       
def reset_choice(state):
    state.url_selections[state.index] = -1
    state.title_selections[state.index] = -1
    state.image_selections[state.index] = -1

def display_choice(state):
    params = state.all_params[state.index]
    st.subheader(f'Page {state.index+1}: Which do you prefer?')

    urls = params[0]
    titles = params[1]
    pics = params[2]
    
    picked = -1
    cols = st.beta_columns(4)
    for i in range(4):
        with cols[i]:
            st.image([pics[i]], use_column_width=True)
            if st.button("{}".format(titles[i].capitalize())):
                picked = i
    
    # increment and update selections
    if picked >= 0 and state.index < state.num_pages:
        st.write(f"You picked: {titles[picked].capitalize()}")
        state.url_selections[state.index] = urls[picked]
        state.title_selections[state.index] = titles[picked].capitalize()
        state.image_selections[state.index] = pics[picked]

def display_results(state):
    st.title('Final Recommendations')
    
    row1 = st.beta_columns(5)
    row2 = st.beta_columns(5)
    
    rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(state.url_selections)

    for i in range(5):
        with row1[i]:
            st.image([rec_image_paths[i]], use_column_width=True)
            st.write(f"[{rec_titles[i]}]({rec_urls[i]})")
        with row2[i]:
            st.image([rec_image_paths[5+i]], use_column_width=True)
            st.write(f"[{rec_titles[5+i]}]({rec_urls[5+i]})")
    
    st.title('Your Choices')
    row3 = st.beta_columns(5)
    
    for i in range(5):
        with row3[i]:
            st.image([state.image_selections[i]], use_column_width=True)
            st.write(f"[{state.title_selections[i]}]({state.url_selections[i]})")

def display(state, message):
    if state.index == state.num_pages:
        display_results(state)
    else:
        display_choice(state)
    st.write(message)
    # st.write(state.title_selections)

def main():
    num_pages = 5
    state = SessionState.get(rec_sys = KNNRecSys(),
                             all_params = {idx: get_images(idx) for idx in range(num_pages)},
                             index = 0, 
                             url_selections = [-1 for _ in range(num_pages)],
                             title_selections = [-1 for _ in range(num_pages)],
                             image_selections = [-1 for _ in range(num_pages)],
                             num_pages = num_pages 
                            )
    
    message = ""

    b, r, f = st.beta_columns(3)
    with b:
        if st.button('Back') and state.index > 0:
            state.index = state.index - 1
    with r:
        if st.button('Refresh'):
            state.all_params[state.index] = get_images(state.index)
            reset_choice(state)
    with f:
        if st.button('Forward') and state.index < num_pages:
            if state.title_selections[state.index] != -1:
                state.index = state.index + 1
            else:
                message = "Please make a selection"

    my_bar = st.progress(state.index / state.num_pages)
    display(state, message)

    
main()