import flask
from flask import render_template, request, Flask, g, url_for

import time
import os
import json
import random
import sys
import traceback
import sqlite3

import models_elastic as nakatomidb

from datetime import datetime

from mythril.ethereum.interface.rpc.client import EthJsonRpc
infura=EthJsonRpc("mainnet.infura.io", 443, True)

app = Flask(__name__,static_url_path='/static')
app.config.from_object('config')
app.jinja_env.add_extension('jinja2.ext.do')

conn = sqlite3.connect('coverage.db',check_same_thread=False)
#c = conn.cursor()

@app.before_request
def before_request():
  g.preview_length = app.config['PREVIEW_LENGTH']

@app.before_first_request
def before_first_request():
  print("creating/fixing coverage db")
  #conn = sqlite3.connect('coverage.db')
  c = conn.cursor()

  print("creating coverage table")
  try:
    c.execute('''CREATE TABLE mainnet
      (block integer primary key autoincrement,
       slotted bool default 0,
       filled bool default 0,
       mtime datetime )''')
    print(" done")
  except Exception as e:
    print(" oops: "+str(e))

  infura=EthJsonRpc("mainnet.infura.io", 443, True)
  currentblock=infura.eth_blockNumber()

  result = c.execute("select count(*) from mainnet")
  coveragecount = result.fetchone()[0]

  print("last known block is "+str(currentblock))
  print("last known coverage at "+str(coveragecount))
 
  for x in range(coveragecount,currentblock):
    c.execute('insert into "mainnet" default values')
  print("coverage updates complete")
  conn.commit()
  #conn.close()


# Create your views here.
@app.route('/host')
def host():
  host = request.args.get('h')
  context = nakatomidb.gethost(host)
  return render_template("host.html",**context)

@app.route('/')
def search():
  query = request.args.get('q', '')
  page = int(request.args.get('p', 1))
  format = request.args.get('f', "")

  searchOffset = app.config['RESULTS_PER_PAGE'] * (page-1)

  try:
    count,context = nakatomidb.search(query,app.config['RESULTS_PER_PAGE'],searchOffset)
  except:
    return "error connecting to elasticdb"

  next_url = url_for('search', q=query, p=page + 1) \
      if count > page * app.config['RESULTS_PER_PAGE'] else None
  prev_url = url_for('search', q=query, p=page - 1) \
      if page > 1 else None

  # what kind of output are we looking for?
  if format == 'hostlist':
    return render_template("hostlist.html",query=query, numresults=count, page=page, hosts=context)
  else:
    return render_template("search.html",query=query, numresults=count, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

@app.route('/getwork')
def getwork():

  c = conn.cursor()

  # init the db
  infura=EthJsonRpc("mainnet.infura.io", 443, True)
  currentblock=infura.eth_blockNumber()

  result = c.execute("select count(*) from mainnet")
  coveragecount = result.fetchone()[0]

  print("last known block is "+str(currentblock))
  print("last known coverage at "+str(coveragecount))

  for x in range(coveragecount,currentblock):
    c.execute('insert into "mainnet" default values')
  print("coverage updates complete")

  # clean up slots
  c.execute("update mainnet set slotted = false, mtime = 0 where slotted = true and filled = false and mtime < ? ",(round(time.time()-60*60),)) # wait one hour for slot submission

  # reserve the next slot
  result = c.execute("select max(block) from mainnet where slotted = false")
  newwork = result.fetchone()[0]
  print("new work is "+str(newwork))
  c.execute("update mainnet set slotted = true, mtime = ? where block = ?",(round(time.time()),newwork))
  conn.commit()

  work = {}
  work['type']='karl'
  work['block']=newwork
  return json.dumps(work)

@app.route('/submit',methods=['POST'])
def submit():

  data = request.get_json()
  newscan={}
  newscan=json.loads(data)
  newscan['ctime'] = datetime.now()
  nakatomidb.newscan(newscan)

  c = conn.cursor()
  c.execute("update mainnet set filled = true, mtime = ? where block = ?",(round(time.time()),newscan['block']))
  conn.commit()

  data = request.get_json()

  return "[+] added scan data"
