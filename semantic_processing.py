import os, logging
import retinasdk
from collections import OrderedDict
import six

def table_summary(vv0):
    tablesummary = {}
    tablesummary["header"]  = vv0["header"]
    tablesummary["captions"]  = " ".join(vv0["captions"])
    tablesummary["text_cells"] = ""
    for vv1 in vv0["data"]: 
        #logging.debug([ cell["value"] for cell in vv1  if (cell["type"] == "other") or (cell["type"] == "complex")] )
        tablesummary["text_cells"] += \
            " ".join([ cell["value"] for cell in vv1  if (cell["type"] == "other") or (cell["type"] == "complex")])
    return tablesummary

def text_from_table(table):
    return " ".join( table_summary(table).values() )


def connect_to_retina( full = False,
        apiServer="http://api.cortical.io/rest", retinaName="en_associative",
        **kwargs):
    try:  
        os.environ["RETINA_SDK_KEY"]
    except KeyError: 
        print( "Please set the environment variable RETINA_SDK_KEY", file = sys.stderr)
    retina_sdk_key = os.environ['RETINA_SDK_KEY']

    if full:
        client = retinasdk.FullClient
    else:
        client = retinasdk.LiteClient

    return client(retina_sdk_key, apiServer=apiServer, retinaName=retinaName, **kwargs )
 
def get_footprint_of_tables( tabledict ):
    
    liteClient =  connect_to_retina()
    for kk, vv in six.iteritems(tabledict):
        table_text = text_from_table(vv)
        yield ( kk, liteClient.getFingerprint( table_text.encode('ascii', 'ignore')   ) )
