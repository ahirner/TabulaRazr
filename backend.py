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
import logging

config = { "min_delimiter_length" : 4, "min_columns": 2, "min_consecutive_rows" : 3, "max_grace_rows" : 4,
          "caption_assign_tolerance" : 10.0, "meta_info_lines_above" : 8, "threshold_caption_extension" : 0.45,
         "header_good_candidate_length" : 3, "complex_leftover_threshold" : 2, "min_canonical_rows" : 0.2}


def read_lines( test_file ):
    with open(test_file) as ff: 
        for line in ff:
            yield line

# ## Tokenize and Tag ##

# In[4]:

#Regex tester online: https://regex101.com
#Contrast with Basic table parsing capabilities of http://docs.astropy.org/en/latest/io/ascii/index.html

tokenize_pattern = "[.]{%i,}|[\ \$]{%i,}|" % ((config['min_delimiter_length'],)*2)
tokenize_pattern = "[.\ \$]{%i,}" % (config['min_delimiter_length'],)
footnote_inidicator = "[^,_!a-zA-Z0-9.]"

column_pattern = OrderedDict()
#column_pattern['large_num'] = u"\d{1,3}(,\d{3})*(\.\d+)?"
column_pattern['large_num'] = "(([0-9]{1,3})(,\d{3})+(\.[0-9]{2})?)"
column_pattern['small_float'] = "[0-9]+\.[0-9]+"
column_pattern['integer'] = "^\s*[0-9]+\s*$"
#column_patter['delimiter'] = "[_=]{6,}"
#column_pattern['other'] = u"([a-zA-Z0-9]{2,}\w)"
column_pattern['other'] = ".+"

subtype_indicator = OrderedDict()
subtype_indicator['dollar'] = ".*\$.*"
subtype_indicator['rate'] = "[%]"
#enter full set of date patterns here if we want refinement early on
subtype_indicator['year'] = "(20[0-9]{2})|(19[0-9]{2})"


# In[5]:

#import dateutil.parser as date_parser
#Implement footnote from levtovers
def tag_token(token, ws):
    for t, p in column_pattern.items():
        result = re.search(p, token)
        if result:
            leftover = token[:result.start()], token[result.end():]
            lr = "".join(leftover)
            value = token[result.start():result.end()]

            if len(lr) >= config['complex_leftover_threshold']:
                return "complex", "unknown", token, leftover

            subtype = "none"
            #First match on left-overs
            for sub, indicator in subtype_indicator.items():
                if re.match(indicator, lr): subtype = sub
            #Only if no indicator matched there, try on full token
            if subtype == "none":
                for sub, indicator in subtype_indicator.items():
                    if re.match(indicator, token): subtype = sub
            #Only if no indicator matched again, try on whitespace
            if subtype == "none":
                for sub, indicator in subtype_indicator.items():
                    if re.match(indicator, ws): subtype = sub
            #print token, ":", ws, ":", subtype

            return t, subtype, value, leftover
    return "unknown", "none", token, ""

def row_feature(line):
    matches = re.finditer(tokenize_pattern, line)
    start_end = [ (match.start(), match.end()) for match in matches]
    #No delimiter found so it's free flow text
    if len(start_end) < 1:
        if len(line) == 0:
            return []
        else:
            return [{'start' : 0, 'value' : line, 'type' : 'freeform', 'subtype' : 'none'}]

    tokens = re.split(tokenize_pattern, line)
    if tokens[0] == "":
        tokens = tokens[1:]
    else:
        start_end = [(0,0)] + start_end

    features = []
    for se, token in zip(start_end, tokens):
        t, subtype, value, leftover = tag_token(token, line[se[0]:se[1]])
        feature = {"start" : se[1], "value" : value, "type" : t, "subtype" : subtype, "leftover" : leftover}
        features.append(feature)
    return features


# In[6]:

#Establish whether amount of rows is above a certain threshold and whether there is at least one number
def row_qualifies(row):
    return len(row) >= config['min_columns'] and sum( 1 if c['type'] in ['large_num', 'small_float', 'integer'] else 0 for c in row) > 0

def row_equal_types(row1, row2):
    same_types = sum ([1 if t[0]==t[1] else 0 for t in ((c1['type'], c2['type']) for c1, c2 in zip(row1, row2))])
    return same_types


""" Scope """


#Non qualified rows arm for consistency check but are tolerated for max_grace_rows (whitespace, breakline, junk)
def filter_row_spans_new(row_features, row_qualifies=row_qualifies, ):

    min_consecutive = config["min_consecutive_rows"]
    grace_rows = config['max_grace_rows']

    last_qualified = None
    consecutive = 0
    underqualified = 0
    consistency_check = False
    i = 0

    for j, row in enumerate(row_features):
        qualifies = row_qualifies(row)
        if consistency_check:
            print("BENCHMARKING %s AGAINST:" % row_to_string(row), row_to_string(row_features[last_qualified], 'type'))
            if not row_type_compatible(row_features[last_qualified], row):
                qualifies = False
            consistency_check = False
        #print qualifies, row_to_string(row)

        if qualifies:
            if last_qualified is None:
                last_qualified = i
                consecutive = 1
            else:
                consecutive += 1
        else:
            underqualified += 1
            if underqualified > grace_rows:
                if consecutive >= min_consecutive:
                    #TODO: do post splitting upon type check and benchmark
                    print("YIELDED from", last_qualified, "to", i-underqualified+1)
                    yield last_qualified, i-underqualified+1

                last_qualified = None
                consecutive = 0
                underqualified = 0
                consistency_check = False
            else:
                if last_qualified:
                    consistency_check = True
        logging.debug(i, last_qualified, consecutive, consistency_check, row_to_string(row))
        i += 1

    if consecutive >= min_consecutive:
        yield last_qualified, i-underqualified

def row_to_string(row, key='value', sep='|'):
    return sep.join(c[key] for c in row)

def row_type_compatible(row_canonical, row_test):
    #Test whether to break because types differ too much
    no_fit = 0
    for c in row_test:
        dist = (abs(c['start']-lc['start']) for lc in row_canonical)
        val, idx = min((val, idx) for (idx, val) in enumerate(dist))
        if c['type'] != row_canonical[idx]['type']:
            no_fit += 1

    fraction_no_fit = no_fit / float(len(row_test))
    #print "test row", row_to_string(row_test), ") against types (", row_to_string(row_canonical, 'type'), ") has %f unmatching types" % fraction_no_fit
    return fraction_no_fit < config["threshold_caption_extension"]

def filter_row_spans(row_features, row_qualifies):

    min_consecutive = config["min_consecutive_rows"]
    grace_rows = config['max_grace_rows']

    last_qualified = None
    consecutive = 0
    underqualified = 0
    underqualified_rows = [] #Tuples of row number and the row

    i = 0

    for j, row in enumerate(row_features):
        if row_qualifies(row):
            underqualified = 0
            if last_qualified is None:
                last_qualified = i
                consecutive = 1
            else:
                consecutive += 1
        else:
            underqualified += 1
            underqualified_rows.append((j, row) )
            if underqualified > grace_rows:
                if consecutive >= min_consecutive:
                    yield last_qualified, i-underqualified+1

                last_qualified = None
                consecutive = 0
                underqualified = 0
        logging.debug(i, underqualified, last_qualified, consecutive)#, "" or row
        i += 1

    if consecutive >= min_consecutive:
        yield last_qualified, i-underqualified


# In[8]:

def row_to_string(row, key='value', sep='|'):
    return sep.join(c[key] for c in row)


"""Structure"""

def readjust_cols(feature_row, slots):

    feature_new = [{'value' : 'NaN'}] * len(slots)
    for v in feature_row:
        dist = (abs((float(v['start'])) - s) for s in slots)
        val , idx = min((val, idx) for (idx, val) in enumerate(dist))
        if val <= config['caption_assign_tolerance']: feature_new[idx] = v

    return feature_new


def normalize_rows(rows_in, structure):
    slots = [c['start'] for c in structure]
    nrcols = len(structure)

    for r in rows_in:
        if len(r) != nrcols:
            if len(r)/float(nrcols) > config['threshold_caption_extension']:
                yield readjust_cols(r, slots)
        else:
            yield r

#TODO: make side-effect free
def structure_rows(row_features, meta_features):
    #Determine maximum nr. of columns
    lengths = Counter(len(r) for r in row_features)
    nrcols = config['min_columns']
    for l in sorted(list(lengths.keys()), reverse=True):
        nr_of_l_rows = lengths[l]
        if nr_of_l_rows/float(len(row_features)) > config['min_canonical_rows']:
            nrcols = l
            break

    canonical = [r for r in row_features if len(r) == nrcols]

    #for c in canonical: print len(c), row_to_string(c)

    structure = []
    for i in range(nrcols):
        col = {}
        col['start'] = float (sum (c[i]['start'] for c in canonical )) / len(canonical)

        types = Counter(c[i]['type'] for c in canonical)
        col['type'] = types.most_common(1)[0][0]
        subtypes = Counter(c[i]['subtype'] for c in canonical if c[i]['subtype'] is not "none")
        subtype = "none" if len(subtypes) == 0 else subtypes.most_common(1)[0][0]
        col['subtype'] = subtype
        structure.append(col)

    #Test how far up the types are compatible and by that are data vs caption
    for r in row_features:
        #if r in canonical:
        if len(r) and row_type_compatible(structure, r):
            break
        else:
            meta_features.append(r)
            row_features.remove(r)

    meta_features.reverse()
    #for m in meta_features: print "META", row_to_string(m)

    captions = [''] * nrcols
    single_headers = []
    latest_caption_len = 1
    slots = [c['start'] for c in structure]
    for mf in meta_features:
        #if we have at least two tokens in the line, consider them forming captions
        nr_meta_tokens = len(mf)
        if nr_meta_tokens > 1 and nr_meta_tokens >= latest_caption_len:
            #Find closest match: TODO = allow doubling of captions if it is centered around more than one and len(mf) is at least half of nrcols
            for c in mf:
                dist = (abs((float(c['start'])) - s) for s in slots)
                val, idx = min((val, idx) for (idx, val) in enumerate(dist))
                if val <= config['caption_assign_tolerance']:
                    captions[idx] = c['value'] + ' ' + captions[idx]
                else: single_headers.append(c['value'])
            #latest_caption_len = nr_meta_tokens
        #otherwise, throw them into headers directly for now
        else:
            #Only use single tokens to become headers, throw others away
            if len(mf) == 1 and mf[0]['type'] != 'freeform': single_headers.append(mf[0]['value'])


    #Assign captions as the value in structure
    for i, c in enumerate(captions):
        structure[i]['value'] = c
    #Expand all the non canonical rows with NaN values (Todo: if types are very similar)
    normalized_data = [r for r in normalize_rows(row_features, structure)]

    return structure, normalized_data, single_headers


def convert_to_table(rows, b, e, above):
    table = {'begin_line' : b, 'end_line' : e}

    data_rows = rows[b:e]
    meta_rows = rows[b-above:b]

    structure, data, headers = structure_rows(data_rows, meta_rows)

    captions = [(col['value'] if 'value' in list(col.keys()) else "---") for col in structure]
    types = [col['type'] for col in structure]
    subtypes = [col['subtype'] for col in structure]
    table['types'] = types
    table['subtypes'] = subtypes
    table['captions'] = captions
    table['data'] = data
    table['header'] = " | ".join(headers)

    return table

def indexed_tables_from_rows(row_features):

    #Uniquely identify tables by their first row
    tables = OrderedDict()
    last_end = 0
    for b,e in filter_row_spans(row_features, row_qualifies):
        #Slice out the next table and limit the context rows to have no overlaps
        #Todo: manage the lower meta lines
        tables[b] = convert_to_table(row_features, b, e, min(config['meta_info_lines_above'], b - last_end))
        last_end = tables[b]['end_line']
    return tables

def parse_tables(txt_path):

    #Uniquely identify tables by their first row
    tables = OrderedDict()

    with codecs.open(txt_path, "r", "utf-8") as f:
        lines = [l.replace('\n', '').replace('\r', '') for l in f]
        rows = [row_feature(l) for l in lines]

        return indexed_tables_from_rows(rows)

def table_to_df(table):
    df = pd.DataFrame()
    for i in range(len(table['captions'])):
        values = []
        for r in table['data']:
            values.append(r[i]['value'])
        df[i] = values
    df.columns = table['captions']
    return df


def get_all_tables( uploaddir , suffix = ".table.json"):
    listing1 = os.listdir( uploaddir )
    tablekeys = []
    #projectkeys =  [ x in listing1 if os.path.isdir(x) ]
    for ff in os.listdir( uploaddir ):
        if ff.endswith(suffix):
            key = ff.replace(suffix, "")
            #print( key )
            yield key 
            continue
    for x in os.walk( uploaddir ):
        for dd  in x[1]:
            for ff in os.listdir( os.path.join( uploaddir, dd) ) :
                if ff.endswith(suffix):
                    key = os.path.join( dd, ff.replace( suffix, "") )
                    #print( key)
                    yield key   
                    continue

        for pp  in x[1]:
            for dd in filter( lambda x: os.path.isdir( x ) , os.listdir( os.path.join( uploaddir,pp)) ):
                for ff in os.listdir( os.path.join( uploaddir, pp,  dd) ) :
                    if ff.endswith(suffix):
                        key = os.path.join( dd, ff.replace( suffix, "") )
                        #print( key)
                        yield key   
                        continue

def _cast_num_(ds, thousandsep = ",", decimalsep = "."):
    "casts a pandas Series to numeric"
    ds = ds.map(lambda x: x.replace(thousandsep, ""))
    if ds.map(lambda x : decimalsep in x).any():
        return ds.astype(float)
    else:
        return ds.astype(int)
    
def _subset_numeric_bloc_(df, thr = 1/4):
    "returns a numeric part, leaving data un-casted"
    isnumericcol = df.applymap(isnumeric).mean() > 1- thr
    isnumericrow = df.loc[:,isnumericcol].applymap(isnumeric).all(1)
    return df.loc[isnumericrow,isnumericcol]

def subset_and_cast_numeric_bloc(df, thousandsep = ",", decimalsep = ".", thr = 1/4):
    "takes a numeric part of the table and casts it into numeric types (int or float)"
    dfnum = _subset_numeric_bloc_(df, thr = thr)
    caster = lambda ds: _cast_num_(ds, thousandsep = thousandsep, decimalsep = decimalsep)
    for ii in range(len(dfnum.columns)):
        dfnum.iloc[:,ii] = caster(dfnum.iloc[:,ii])
    return dfnum


