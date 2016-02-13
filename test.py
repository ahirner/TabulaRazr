#!/usr/bin/env python
# coding: utf-8


#DocX - TABLE Parser
#Infers a table with arbitrary number of columns from reoccuring patterns in text lines
#(c) Alexander Hirner 2016, no redistribution without permission

#Main assumptions Table identificatin:
#1) each row is either in one line or not a row at all
#2) each column features at least one number (=dollar amount)
#2a) each column features at least one date-like string [for time-series only]
#3) a table exists if rows are in narrow consecutive order and share similarities --> scoring algo [DONE]
#4) each column is separated by more than x consecutive whitespace indicators (e.g. '  ' or '..')

#Feature List Todo:
#1) Acknowledge footnotes / make lower meta-data available
#2) make delimiter length smartly dependent on number of columns (possible iterative approach)
#3) improve captioning: expand non canonical values in tables [DONE] .. but not to the extent how types match up  --> use this to further
## delineate between caption and headers
#4) UI: parameterize extraction on the show page on the fly
#5) deeper type inference on token level: type complex [DONE], subtype header (centered, capitalized),
## subtype page nr., type free flow [DONE, need paragraph]
#5a) re
#6) Respect negative values with potential '-' for numerical values
#7)
#8) classify tables with keywords (Muni Bonds) and unsupervised clustering (Hackathon)

from __future__ import print_function
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


# ## Tests ##

from IPython.display import display

#print i, underqualified, last_qualified, consecutive#, "" or row
test_file = "testcases/test_input1.txt"
test_string = read_lines( test_file )
rows = [row_feature(l) for l in test_string]

for b, e in filter_row_spans(rows, row_qualifies):
    print(b, row_to_string(rows[b]), " --> ", e, row_to_string(rows[e]))
    #for i in range(b,e):
    #    print i, len(rows[i]), row_to_string(rows[i])

print("#######################")

tables = indexed_tables_from_rows(rows)
for begin_line, t in tables.items():
    df = table_to_df(t)

    #for d in t['data']: print row_to_string(d)

    for j in range(t['begin_line']-4, t['begin_line']):
        pass

    for j in range(t['begin_line'], t['end_line']):
        pass #print len(rows[j]), test_string[j], "|".join([c['type']+'_'+c['subtype'] for c in rows[j]])
    print(t['header'])
    display(df)


try:
    from IPython.display import display
    test_file = "testcases/test_input6.txt"
    test_string = read_lines( test_file )
    rows = [row_feature(l) for l in test_string]

    tables = indexed_tables_from_rows(rows)
    for begin_line, t in tables.items():
        df = table_to_df(t)

        for j in range(t['begin_line']-4, t['begin_line']):
            print(len(rows[j]), rows[j])

        for j, row in enumerate(t['data']):
            print(len(rows[t['begin_line'] + j]), rows[t['begin_line'] + j])
        print(t['header'])
        display(df)
except:
    pass
