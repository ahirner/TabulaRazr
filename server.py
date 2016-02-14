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
3) a table exists if rows are in narrow consecutive order and share 
arities --> scoring algo [DONE]
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
import sys, os, re, six

import codecs
import string

from collections import Counter, OrderedDict

import json
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename
from flask import jsonify, render_template, make_response

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from backend import parse_tables, table_to_df
import  semantic_processing  as sempr
#import get_footprint_of_tables, get_nearest_neighbors


config = { "min_delimiter_length" : 4, "min_columns": 2, "min_consecutive_rows" : 3, "max_grace_rows" : 4,
          "caption_assign_tolerance" : 10.0, "meta_info_lines_above" : 8, "threshold_caption_extension" : 0.45,
         "header_good_candidate_length" : 3, "complex_leftover_threshold" : 2, "min_canonical_rows" : 0.2}


""" Web App """

scripts = []
css = [
    "./thirdparty/bootstrap/dist/css/bootstrap.min.css",
    "./thirdparty/metisMenu/dist/metisMenu.min.css",
    "./thirdparty/startbootstrap-sb-admin-2/dist/css/timeline.css",
    "./thirdparty/startbootstrap-sb-admin-2/dist/css/sb-admin-2.css",
    "./thirdparty/morrisjs/morris.css",
    "./thirdparty/font-awesome/css/font-awesome.min.css",
    "./thirdparty/lf-ng-md-file-input/dist/lf-ng-md-file-input.css",
    "./thirdparty/angular-material/angular-material.min.css",
    "./css/new.css"
]

js = [
    "./thirdparty/angular/angular.js",
    "./thirdparty/angular-ui-router/release/angular-ui-router.js",
    "./js/app.js",
    "./js/controller.js",
    "./js/browser/controller.js",
    "./js/browser/BrowserDirective.js",
    "./thirdparty/lf-ng-md-file-input/dist/lf-ng-md-file-input.js",
    "./thirdparty/angular-animate/angular-animate.min.js",
    "./thirdparty/angular-aria/angular-aria.min.js",
    "./thirdparty/angular-material/angular-material.min.js",
    "./thirdparty/ng-file-upload/ng-file-upload.js",
]


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


def basename(filename):
    filename = secure_filename(filename)
    filebase = filename.replace(".pdf","").replace(".txt", "")
    return filebase

class InputFile():
    def __init__(self, upload, project , filename):

        self.upload = upload

        self.project_key = project if project is not None else "-"

        self.project = project if (project is not None and project is not "-") else ""
        self.filename = filename

    @property
    def basename(self):
        """ mybonds.pdf -> mybonds """
        self.filename = secure_filename( self.filename)
        filebase = self.filename.replace(".pdf","").replace(".txt", "")
        return filebase
    
    @property
    def filedir(self):
        """ directory where tables from one source file are stored"""
        return  os.path.join( self.upload, self.project, self.basename )

    @property
    def projdir(self):
        """ directory where tables from one source file are stored"""
        return  os.path.join( self.upload, self.project, )

    @property
    def filepath( self ):
        """ the path to the raw pdf file"""
        return  os.path.join( self.filedir)


   
@app.route('/', methods=['GET', 'POST'])
def upload_file():

    if request.method == 'POST':
        
        file = request.files['file']
        project = request.form['project']
        
        if file and allowed_file(file.filename):
            extension = get_extension(file.filename)
            filename = secure_filename(file.filename)

            upload = app.config['UPLOAD_FOLDER']
            project = request.args.get('project')
            inp = InputFile(upload, project, filename)
            filebase = inp.basename
            filedir = inp.filedir

            if not os.path.isdir( filedir ):
                os.makedirs(filedir)

            filepath = inp.filepath
            file.save( filepath )
             
            if extension == "pdf":
                txt_path = filepath + '.txt'
                filename += '.txt'        
                if not os.path.isfile(txt_path):
                    #Layout preservation crucial to preserve clues about tabular data
                    cmd = "pdftotext -enc UTF-8 -layout %s %s " % ( filepath , txt_path)
                    
                    print( cmd , file = sys.stderr)
                    os.system(cmd)            
                else:
                    print( "skipping conversion" , file = sys.stderr)

            return redirect(url_for('analyze', filename=filename, project=project))

    return render_template('index.html',
        title=TITLE ,
        css=css,
        js=js)

# + project, table_id in the query string <--- not anymore, 
@app.route('/api/get_table/<project>/<filename>/<table_id>', methods=['GET', 'POST'])
def get_table(filename, project, table_id):
    if project == "-":
        project = None
    return json.dumps(get_table_frontend(project, filename, table_id))

@app.route('/api/get_similar_tables_all/<project>/<filename>/<table_id>', methods=['GET', 'POST'])
def get_similar_tables_all(filename, project, table_id):


    upload = app.config['UPLOAD_FOLDER']
    inp = InputFile(upload, project, filename)
    tables = [get_table_frontend(pr, fn, t_id) for fn, pr, t_id in \
                        sempr.get_nearest_neighbors(inp, table_id, True)]
    return json.dumps(tables)
    
    
def get_table_frontend(project, filename, table_id):
            #filepath =  os.path.join( filedir, filename )
    upload = app.config['UPLOAD_FOLDER']
    inp = InputFile(upload, project, filename)

    #table_path = inp.filepath + "/" + table_id + '.table.json'
    table_path = os.path.join( inp.filedir , table_id + '.table.json')
    with codecs.open(table_path) as file:
        table = json.load(file)

    captions = [{ 'value': c } for c in table['captions']]
    for i, c in enumerate(table['captions']):
        captions[i]['type'] = table['types'][i]
        captions[i]['subtype'] = table['subtypes'][i]
        string_collated = (table['types'][i] + table['subtypes'][i])
        sample_color = string_collated[0] + string_collated[-1] + string_collated[ int(len(string_collated)/2) ]
        captions[i]['color'] = "#F%sF%sF%s" % tuple(sample_color)

    rows = []

    for i in range(len(table['data'])):
        row = {}
        for j, c in enumerate(captions):
            row[c['value']] = table['data'][i][j]
        rows.append(row)

    _id = {}
    _id['table_id'] = table_id
    _id['filename'] = filename
    _id['project'] = project

    return {'_id' : _id, 'meta' : captions, 'data' : rows}
   

def page_statistics(table_dict,  lines_per_page = 80):
    nr_data_rows = []
    for key, t in table_dict.items():
        e = t['end_line']
        b = t['begin_line']
        for l in range(b, e):
            page = int(l / lines_per_page)
            if len(nr_data_rows) <= page:
                nr_data_rows += ([0]*(page-len(nr_data_rows)+1))
            nr_data_rows[page] += 1
    chart = pd.DataFrame()
    chart['value'] = nr_data_rows
    chart['page'] = range(0, len(chart))
    return chart 

@app.route('/analyze/<filename>', methods=['GET', 'POST'])
def analyze(filename):   
    upload = app.config['UPLOAD_FOLDER']
    project = request.args.get('project')
    print("project:", project)
    inp = InputFile(upload, project, filename)
    filebase = inp.basename
    filedir = inp.filedir
    filepath = inp.filepath 
    
    if not os.path.isfile( filepath ):
        print( filepath , " not found ", file = sys.stderr )
        return jsonify({'error' : filepath +' not found' })
    
    tables = parse_tables(  filepath )
    
    """Export tables"""
    for kk, vv in six.iteritems(tables):
        table_path = os.path.join( filedir, "%s" % kk)
        print( "table_path" , table_path)
        with codecs.open(table_path + '.table.json', 'w', "utf-8") as file:
            json.dump( vv ,  file)

    #Export chart
    dr = page_statistics(tables,  lines_per_page = 80)

    #plot the row density
    chart_path = os.path.join(filedir, "chart"  + '.png' )

    fig, ax = plt.subplots( nrows=1, ncols=1, figsize=(8,3) )  # create figure & 1 axis
    ax.set_xlabel('page number')
    ax.set_ylabel('number of data rows')
    ax.set_title('Distribution of Data Rows per Page')
    
    BARHEIGHT = 0.4
    ax.stem(1 + np.array(dr['page']) , dr['value'], )

    xticks = np.arange(0, np.ceil(max( dr['page'] )) + 2 )
    ax.set_xticks(xticks)
    ax.set_xlim([0, xticks[-1]] )
    fig.tight_layout()
    fig.savefig( chart_path)   # save the figure to file
    plt.close(fig)                      # close the figure

    #Export fingerprints (use same path as for tables)
    for kk, vv in zip(tables.keys(), sempr.get_footprint_of_tables(tables.values())):
        fingerprint_path = os.path.join( filedir, "%s" % kk)
        print( "fingerprint_path" , fingerprint_path)
        
        with codecs.open(fingerprint_path + '.fingerprint.json', 'w', "utf-8") as file:
            json.dump(vv,  file)
            

    return redirect(url_for('uploaded_file', filename=filename, project=project))

@app.route('/browser')
def test():

    return render_template('index.html',
        TITLE='Semantic-Browser',
        css=css,
        js=js)
    
@app.route('/show/<filename>')
def uploaded_file( filename ):
    upload = app.config['UPLOAD_FOLDER']
    project = request.args.get('project')
    inp = InputFile(upload, project, filename)
    filebase = inp.basename 
    filedir = inp.filedir
    
    def get_tables( filedir, suffix = '.table.json'):
        tablelist = list( filter( lambda x : x.endswith(suffix) , os.listdir( filedir ) ) )
        #if len( tablelist ) == 0:
        #    analyze(path)

        for tf in filter( lambda x : x.endswith(suffix) , os.listdir( filedir ) ):
            with codecs.open( os.path.join(filedir,tf) )  as file:
                table = json.load( file )
                yield table #_to_df(table).to_html()

    tables = get_tables( filedir, suffix = '.table.json')
    dfs = (table_to_df(table).to_html() for table in tables )

    #Create HTML
    notices = ['Extraction Results for ' + filename, 'Ordered by lines']    
    headers = []
    meta_data = []
    for t in get_tables( filedir, suffix = '.table.json') :
        meta_data.append( {'begin_line' : t['begin_line'], 'end_line' : t['end_line']} )
        if 'header' in t:
            headers.append(t['header'])
        else:
            headers.append('-')

    print( "meta_data",  meta_data )
    chart_path = os.path.join(filedir, "chart"  + '.png' )
    return render_template('viewer.html',
        title=TITLE + ' - ' + filename,
        base_scripts=scripts, filename=filename, project=project,
        css=css, notices = notices, tables = dfs, headers=headers, meta_data=meta_data, chart=chart_path)

@app.route('/inspector/<filename>')
def inspector(filename):
    upload = app.config['UPLOAD_FOLDER']
    project = request.args.get('project')
    print("project:", project)
    inp = InputFile(upload, project, filename)
    filebase = inp.basename 
 
    begin_line = int(request.args.get('data_begin'))
    end_line = int(request.args.get('data_end'))
    margin_top = config["meta_info_lines_above"]
    margin_bottom = margin_top

    notices = ['showing data lines from %i to %i with %i meta-lines above and below' % (begin_line, end_line, margin_top)]
    with codecs.open(inp.filepath , "r", "utf-8") as file:
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
    app.debug = True

    if run_from_ipython():
        app.run(host='0.0.0.0', port = 7080) #Borrow Zeppelin port for now
    else:
        PORT = int(os.getenv('PORT', 7080))
        app.run(debug=True, host='0.0.0.0', port = PORT)
