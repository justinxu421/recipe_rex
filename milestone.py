#!/usr/bin/env python
# coding: utf-8
from serve_recs import KNNRecSys
import SessionState

import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import random

@st.cache
def get_images(rec_sys, idx):
    return rec_sys.sample_urls(4)
        
def display(params, state):
    st.title(f'Page {state.index+1}')

    urls = params[0]
    titles = params[1]
    pics = params[2]
    
    col0, col1, col2, col3 = st.beta_columns(4)
    
    with col0:
        st.image([pics[0]], use_column_width=True)
        st.write("{}".format(titles[0].capitalize()))

    with col1:
        st.image(pics[1], use_column_width=True)
        st.write("{}".format(titles[1].capitalize()))
  
    with col2:
        st.image(pics[2], use_column_width=True)
        st.write("{}".format(titles[2].capitalize()))
   
    with col3:
        st.image(pics[3], use_column_width=True)
        st.write("{}".format(titles[3].capitalize()))
        
    st.subheader("Which do you prefer?")
    selection = st.selectbox('', (titles[0], titles[1], titles[2], titles[3]))
    picked = np.where(titles == selection)[0][0]
    state.selections[state.index] = urls[picked]

def display_results(state):
    st.title('Final Recommendations')
    
    row1 = st.beta_columns(5)
    row2 = st.beta_columns(5)
    
    rec_urls, rec_titles, rec_image_paths = state.rec_sys.get_recs(state.selections)

    for i in range(5):
        with row1[i]:
            st.image([rec_image_paths[i]], use_column_width=True)
            st.write("{}".format(rec_titles[i].capitalize()))
        with row2[i]:
            st.image([rec_image_paths[5+i]], use_column_width=True)
            st.write("{}".format(rec_titles[5+i].capitalize()))

#     st.write(rec_urls)
#     st.radio('which image?', rec_urls)
    for i in range(10):
        st.write(f"[{rec_titles[i]}]({rec_urls[i]})")

#     st.write(rec_titles)
#     st.write(rec_image_paths)

def main():
    num_pages = 5
    state = SessionState.get(rec_sys = KNNRecSys(), index = 0, selections = [-1 for _ in range(num_pages)])
    all_params = {idx: get_images(state.rec_sys, idx) for idx in range(num_pages)}
    
    b, f = st.beta_columns(2)
    with b:
        if st.button('Back') and state.index > 0:
            state.index = state.index - 1
            
    with f:
        if st.button('Forward') and state.index < num_pages:
            state.index = state.index + 1
            
    my_bar = st.progress(state.index / num_pages)
    
    if state.index == num_pages:
        display_results(state)
    else:
        display(all_params[state.index], state)
    
#     st.write(state.selections)

main()