import json
from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
import random

def search(query,limit,offset):

  if query=='':
    query='issue' # default search

  try:
    result = es.search(index="nakatomi", doc_type="_doc", body={"size":limit, "from":offset, "query": {"query_string": { 'query':query, "fields":["data"], "default_operator":"AND"  } },"sort": { "ctime": { "order": "desc" }}})
  except:
    return 0,[] # search borked, return nothing

  #result = es.search(index="nmap", doc_type="_doc", body={"size":limit, "from":offset, "query": {"match": {'nmap_data':query}}})
  count = 1

  results=[] # collate results
  for thing in result['hits']['hits']:
    results.append(thing['_source'])

  print("found "+str(result['hits']['total']))
  return result['hits']['total'],results

def newscan(scan):
  es.index(index='nakatomi', doc_type='_doc', id=scan["block"], body=scan)

