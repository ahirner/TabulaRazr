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


# ## Scope ##

# In[7]:

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
        print(i, last_qualified, consecutive, consistency_check, row_to_string(row))
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
        print(i, underqualified, last_qualified, consecutive)#, "" or row
        i += 1

    if consecutive >= min_consecutive:
        yield last_qualified, i-underqualified


# In[8]:

def row_to_string(row, key='value', sep='|'):
    return sep.join(c[key] for c in row)


# ## Structure ##

# In[9]:

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

    captions = [(col['value'] if 'value' in list(col.keys()) else "---") +"\n(%s, %s)" % (col['type'], col['subtype']) for col in structure]
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

def return_tables(txt_path):

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


# ## Web App ##

# In[10]:

# TITLE = "TabulaRazr (docX)"

scripts = []
css = [
    "./thirdparty/bootstrap/dist/css/bootstrap.min.css",
    "./css/new.css"
    #"./css/main.css",
    #"./css/style.css"
]
js = [
    "./thirdparty/angular/angular.js"
]

import matplotlib.pyplot as plt

UPLOAD_FOLDER = './static/ug'
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])

TITLE = "TabulaRazr"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_extension(filename):
    return '.' in filename and            filename.rsplit('.', 1)[1]

def allowed_file(filename):
    return get_extension(filename) in ALLOWED_EXTENSIONS

@app.route('/bower_components/<path:path>')
def send_bower_components(path):
    return send_from_directory('bower_components', path)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print("post for", filename)
            extension = get_extension(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], extension)
            print('trying to write to', path)
            if not os.path.exists(path):
              os.makedirs(path)
            file.save(os.path.join(path, filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename, min_columns=config['min_columns']))

    return render_template('index.html',
        title=TITLE ,
        css=css)

@app.route('/browser')
def test():

    return render_template('semantic-browser.html',
        TITLE='Semantic-Browser',
        css=css,
        js=js)

@app.route('/show/<filename>')
def uploaded_file(filename):
    extension = get_extension(filename)

    pdf_folder = os.path.join(app.config['UPLOAD_FOLDER'], extension)
    txt_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'txt')

    path = os.path.join(pdf_folder, filename)
    txt_path = os.path.join(txt_folder, filename)

    if not os.path.exists(pdf_folder):
      os.makedirs(pdf_folder)
    if not os.path.exists(txt_folder):
      os.makedirs(txt_folder)

    print("showing text", txt_folder)
    
    if extension == "pdf":
        txt_path += '.txt'
        filename += '.txt'
        if not os.path.isfile(txt_path):
            #Layout preservation crucial to preserve clues about tabular data
            cmd = "pdftotext -enc UTF-8 -layout %s %s" % (path, txt_path)
            os.system(cmd)

    min_columns = request.args.get('min_columns')
    tables = return_tables(txt_path)

    #Construct histogram
    lines_per_page = 80
    nr_data_rows = []
    for b, t in tables.items():
        e = t['end_line']
        #print b, e
        for l in range(b, e):
            page = int(l / lines_per_page)
            if len(nr_data_rows) <= page:
                nr_data_rows += ([0]*int(page-len(nr_data_rows)+1))
            nr_data_rows[page] += 1
    dr = pd.DataFrame()
    dr['value'] = nr_data_rows
    dr['page'] = list(range(0, len(dr)))

    #plot the row density
    chart = filename+".png"
    fig, ax = plt.subplots( nrows=1, ncols=1, figsize=(8,3) )  # create figure & 1 axis
    ax.set_xlabel('page nr.')
    ax.set_ylabel('number of data rows')
    ax.set_title('Distribution of Rows with Data')
    ax.plot(dr['page'], dr['value'], )
    fig.savefig('./static/ug/'+chart)   # save the figure to file
    plt.close(fig)                      # close the figure

    #Create HTML
    notices = ['Extraction Results for ' + filename, 'Ordered by lines']
    dfs = (table_to_df(table).to_html() for table in list(tables.values()))
    headers = []
    for t in list(tables.values()):
        if 'header' in t:
            headers.append(t['header'])
        else:
            headers.append('-')
    meta_data = [{'begin_line' : t['begin_line'], 'end_line' : t['end_line']} for t in list(tables.values())]

    return render_template('viewer.html',
        title=TITLE + ' - ' + filename,
        base_scripts=scripts, filename=filename,
        css=css, notices = notices, tables = dfs, headers=headers, meta_data=meta_data, chart='../static/ug/'+chart)

@app.route('/inspector/<filename>')
def inspector(filename):
    extension = 'txt'
    path = os.path.join(app.config['UPLOAD_FOLDER'], extension, filename)
    begin_line = int(request.args.get('data_begin'))
    end_line = int(request.args.get('data_end'))
    margin_top = config["meta_info_lines_above"]
    margin_bottom = margin_top

    notices = ['showing data lines from %i to %i with %i meta-lines above and below' % (begin_line, end_line, margin_top)]
    with codecs.open(path, "r", "utf-8") as file:
        lines = [l.encode('utf-8') for l in file][begin_line - margin_top:end_line + margin_bottom]
        top_lines = lines[:margin_top]
        table_lines = lines[margin_top:margin_top+end_line-begin_line]
        bottom_lines = lines[margin_top+end_line-begin_line:]

    offset = begin_line-margin_top
    table_id = begin_line

    return render_template('inspector.html',
        title=TITLE,
        base_scripts=scripts, css=css, notices = notices, filename=filename, top_lines=top_lines,
        table_lines=table_lines, bottom_lines=bottom_lines, offset=offset, table_id=begin_line)


# In[11]:

def run_from_ipython():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

if run_from_ipython():
    app.run(host='0.0.0.0', port = 7080) #Borrow Zeppelin port for now
else:
    PORT = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port = PORT)


#
# ## Tests ##
# In[ ]:

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
