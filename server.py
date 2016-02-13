#!/usr/bin/env python
# coding: utf-8

"""
DocX - TABLE Parser
Infers a table with arbitrary number of columns from reoccuring patterns in text lines
(c) Alexander Hirner 2016, no redistribution without permission

Main assumptions Table identificatin:
1) each row is either in one line or not a row at all
2) each column features at least one number (=dollar amount)
2a) each column features at least one date-like string [for time-series only]
3) a table exists if rows are in narrow consecutive order and share similarities --> scoring algo [DONE]
4) each column is separated by more than x consecutive whitespace indicators (e.g. '  ' or '..')

Feature List Todo:
1) Acknowledge footnotes / make lower meta-data available
2) make delimiter length smartly dependent on number of columns (possible iterative approach)
3) improve captioning: expand non canonical values in tables [DONE] .. but not to the extent how types match up  --> use this to further
 delineate between caption and headers
4) UI: parameterize extraction on the show page on the fly
5) deeper type inference on token level: type complex [DONE], subtype header (centered, capitalized),
# subtype page nr., type free flow [DONE, need paragraph]
5a) re
6) Respect negative values with potential '-' for numerical values
7)
8) classify tables with keywords (Muni Bonds) and unsupervised clustering (Hackathon)
"""

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


from backend import return_tables, table_to_df


config = { "min_delimiter_length" : 4, "min_columns": 2, "min_consecutive_rows" : 3, "max_grace_rows" : 4,
          "caption_assign_tolerance" : 10.0, "meta_info_lines_above" : 8, "threshold_caption_extension" : 0.45,
         "header_good_candidate_length" : 3, "complex_leftover_threshold" : 2, "min_canonical_rows" : 0.2}


""" Web App """

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


def run_from_ipython():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

if __name__ == "__main__":
    if run_from_ipython():
        app.run(host='0.0.0.0', port = 7080) #Borrow Zeppelin port for now
    else:
        PORT = int(os.getenv('PORT', 8000))
        app.run(debug=True, host='0.0.0.0', port = PORT)
