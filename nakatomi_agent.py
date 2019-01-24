#!/usr/bin/python3

import sys
import requests
import subprocess
import time
import os
import random
import string
import json
import base64

import threading
import multiprocessing
import multiprocessing.pool

try:
  import ipaddress
except:
  print("[!] ipaddress module not found")
  sys.exit()

def scan():
  server="http://127.0.0.1:5000"
  print("[+] Fetching Target from %s" % server)
  target_data = json.loads(requests.get(server+"/getwork").text)
  target = target_data["block"]
  #target = str(7118237)
  print("[+] Target: "+str(target))

  #command = ["nmap","-oA","data/nweb."+rand,"-A","-open",target]
  command = ["python3","karl.py","--rpc","infura-mainnet","-vvvv","--block",target]

  process = subprocess.Popen(command,stdout=subprocess.PIPE)
  try:
    out, err = process.communicate(timeout=60*60) # 1 hour
  except:
    try:
      print("[+] (%s) Killing slacker process" % target)
      process.kill()
    except:
      pass

  print("[+] Scan Complete: " + target)
  print(out)

  result={}
  result["block"]=target
  result["data"]=str(out)

  # submit result
  print("[+] (%s) Submitting work" % target)
  response=requests.post(server+"/submit",json=json.dumps(result)).text
  print("[+] (%s) Response:\n%s" % (target, response))

def main():
  while True:
    if threading.active_count() < 3:
      notifylock=False
      print("[+] Active Threads: %s" % threading.active_count())
      t = threading.Thread(target=scan)
      t.start()
    else:
      if notifylock is False:
        print("[+] Thread pool exhausted")
      notifylock=True

    time.sleep(1)

if __name__ == "__main__":
  main()
