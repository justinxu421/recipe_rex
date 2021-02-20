#!/usr/bin/env python
# coding: utf-8

# In[20]:


import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import random


# In[21]:


col1, col2, col3 = st.beta_columns(3)
pics = ["lumpia.jpg", "pho.jpg", "tofu.jpg"]
# random.shuffle(pics)
picked = [False] * len(pics)

with col1:
    st.header("1.")
    st.image([pics[0]], use_column_width=True)
    if st.checkbox('do u like this?'):
        picked[0] = True

with col2:
    st.header("2.")
    st.image(pics[1], use_column_width=True)
    if st.checkbox('what about this?'):
        picked[1] = True

with col3:
    st.header("3.")
    st.image(pics[2], use_column_width=True)
    if st.checkbox('dis?'):
        picked[2] = True
        
if st.button('Done!'):
    st.write('Loading ...')
    st.header('Based on your choices, this is what we recommend!')

    pics_picked = [pic for i, pic in enumerate(pics) if picked[i] == True]
    st.image(pics_picked, use_column_width=100, caption=["some generic text"] * len(pics_picked))


# In[22]:





# In[ ]:





# In[ ]:




