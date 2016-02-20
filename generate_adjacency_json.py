
from __future__ import print_function
import sys, os, logging, json
import codecs
import numpy as np

from semantic_processing import get_footprint_of_table, text_from_table, connect_to_retina
from backend import get_all_tables

NxN = 502141
uploaddir = "static/ug"

def read_json_table(table_path):
    if table_path is None:
        return {}
    with codecs.open(table_path) as file:
        return json.load(file)

def get_table_path_from_key(key, uploaddir =  "static/ug", suffix = ".table.json" ):
    return os.path.join(uploaddir, key + suffix )

def using_nonzero(x):
    rows,cols = x.nonzero()
    for row,col in zip(rows,cols):
        yield (row,col, x[row,col])

def using_coo(x):
    cx = scipy.sparse.coo_matrix(x)    
    for i,j,v in zip(cx.row, cx.col, cx.data):
        yield (i,j,v)

def get_similarity_matrix(footprints ):
    sim = np.nan*np.ones([len(footprints)]*2)
    for kk1, ff1 in enumerate( footprints):
        for kk2, ff2 in enumerate( footprints):
            #if kk1>kk2:
                #sim[kk1, kk2] = len(set(ff1) and set(ff2)) / NxN
            sim[kk1, kk2] = len(set(ff1) and set(ff2)) /(min(len(ff1), max(ff2))) # NxN
    return sim

if __name__ == "__main__":
    jsonout = "visualization/adj.json" 

    tables = get_all_tables( uploaddir)

    liteconn =  connect_to_retina()
    footprints = [get_footprint_of_table(read_json_table(get_table_path_from_key(key)), liteconn) for key in tables]

    print( sum(1 for e in get_all_tables( uploaddir)) )
    print( len(footprints))

    sim = get_similarity_matrix(footprints )

    graphdict = dict( nodes =[{"name": x, "group" : x.split("/")[-2]} for x in get_all_tables( uploaddir)],
        links = [{"source": int(x[0]), "target": int(x[1]), "value": float(x[-1])} for x in using_nonzero(sim)]
            )

    with open(jsonout, "w") as fp:
        json.dump( graphdict ,  fp)


