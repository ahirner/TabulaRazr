from __future__ import print_function
import os, logging
import retinasdk
from collections import OrderedDict
import six
import sys
import server as srv

def table_summary(vv0):
    tablesummary = {}
    tablesummary["header"]  = vv0["header"]
    tablesummary["captions"]  = " ".join(vv0["captions"])
    tablesummary["text_cells"] = ""
    for vv1 in vv0["data"]: 
        #logging.debug([ cell["value"] for cell in vv1  if (cell["type"] == "other") or (cell["type"] == "complex")] )
        #print(vv1)
        for cell in vv1:
            if "type" in cell:
                if "type" in cell and  cell["type"] == "other" or cell["type"] == "complex":
                    tablesummary["text_cells"] += cell["value"]
    return tablesummary

def text_from_table(table):
    return " ".join( table_summary(table).values() )


def connect_to_retina( full = False,
        **kwargs):
    try:  
        os.environ["RETINA_SDK_KEY"]
    except KeyError: 
        #Make that permanent for now
        os.environ["RETINA_SDK_KEY"] = "c0f2fcf0-d2bd-11e5-8378-4dad29be0fab"
        print( "Took fallback SDK key for now, set the environment variable RETINA_SDK_KEY", file = sys.stderr)
    retina_sdk_key = os.environ['RETINA_SDK_KEY']

    if full:
        client = retinasdk.FullClient
    else:
        client = retinasdk.LiteClient

    return client(retina_sdk_key,  **kwargs )
 
def get_footprint_of_tables( tables ):
    
    liteClient =  connect_to_retina()
    for vv in tables:
        table_text = text_from_table(vv)
        yield liteClient.getFingerprint( table_text.encode('ascii', 'ignore'))

def get_footprint_of_table(table, liteClient = None):
    if liteClient is None:
        liteClient =  connect_to_retina()
    table_text = text_from_table(table)
    return liteClient.getFingerprint( table_text.encode('ascii', 'ignore'))

def get_pref_keys( names, pref = "" ):
    if pref is "":
        return names
    return filter( lambda x: x.startswith( pref + "/"), names )

def  get_suffix_keys( names, suffix = ""):
    if suffix is "":
        return names
    return  filter( lambda x: x.endswith( suffix ), names)


###### RANKING

import json
import codecs
import six
from itertools import chain, islice
from backend import get_all_tables
import operator


#Is inversely correlated to distance
def fingerprint_union_length(fp1, fp2):
    return len(set(chain(fp1,fp2)))

#Not sure about it
def fingerprint_hamming_distance(fp1, fp2):
    edits = 0
    for i in range(TOTAL_BITS_FINGERPRINT):
        if i in fp1 and i not in fp2:
            edits += 1
        if i in fp2 and i not in fp1:
            edits += 1
    return edits

def fingerprint_jaccard_distance(fp1, fp2):
    union = len(set(chain(fp1,fp2)))
    intersect = len(set(fp1) & set(fp2))
    return float(intersect) / union

def get_all_project_tables(project=None):
    
    upload = './static/ug'
            
    inp = srv.InputFile( upload, project, "")

    for s in get_all_tables( inp.projdir ):
        with codecs.open(os.path.join( inp.projdir , s+'.table.json'), "r","utf-8") as file:
            yield s, json.load(file)

def get_nearest_neighbors( inpobj, table_id, exclude_self = False, max = 10):
    
    try:
        project_path = inpobj.projdir
        table_path = os.path.join( inpobj.filedir, table_id +'.fingerprint.json')
        with codecs.open( table_path ,"r","utf-8") as file:
            fingerprint = json.load(file)
            #print(fingerprint)

        similarities = []
        for other_path in get_all_tables( project_path ):
            other_filename, other_table_id = other_path.split(r"/")
            if not (exclude_self and other_table_id == table_id and inpobj.basename == other_filename):
                other_path = os.path.join(project_path, other_filename, other_table_id+'.fingerprint.json')
                try:
                    with codecs.open(other_path, "r","utf-8") as file:
                        other_fp = json.load(file)
                        sim = fingerprint_jaccard_distance(fingerprint, other_fp)
                        similarities.append( (other_filename, other_table_id, sim))
                except:
                    print("Didn't find fingerprint!", other_path)

        similarities.sort(key=operator.itemgetter(2), reverse=True)
        for fn, t_id, sim in islice(similarities, 0, max):
            yield fn, inpobj.project_key, t_id
    except:
        pass