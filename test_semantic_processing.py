
# coding: utf-8

# In[1]:

import sys
import os
import re

import codecs
import string

from collections import Counter, OrderedDict

import json
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename
from flask import jsonify, render_template, make_response

import numpy as np
import pandas as pd
import six

from backend import return_tables, table_to_df
from semantic_processing import get_footprint_of_tables, text_from_table



# In[5]:
try:
    get_ipython().magic('load_ext autoreload')
    get_ipython().magic('autoreload 2')
except:
    pass

# Load data

txt_path = "testcases/test_input4.txt"
tabledict = return_tables(txt_path)

table_to_df(list(tabledict.items())[0][1])

for kk, vv in six.iteritems(tabledict):
    print(kk, text_from_table(vv), sep = "\t")

import os

try:  
    os.environ["RETINA_SDK_KEY"]
except KeyError: 
    print( "Please set the environment variable RETINA_SDK_KEY")

for kk, vv in get_footprint_of_tables(tabledict):
    print(kk, vv, sep = "\t")

