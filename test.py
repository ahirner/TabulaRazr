#!/usr/bin/env python
# coding: utf-8
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

from backend import read_lines, row_feature, filter_row_spans, \
        row_qualifies, row_to_string, indexed_tables_from_rows, table_to_df

""" Tests"""

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
