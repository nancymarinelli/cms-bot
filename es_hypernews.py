#!/usr/bin/env python
import sys, os, re
from datetime import datetime,timedelta
from commands import getstatusoutput
from es_utils import send_payload
from hashlib import sha1
from json import dumps

apache_log_dir="/var/log/httpd"
ssl_error_log = "ssl_error_log"
search_for=" Timeout waiting for output from CGI script "
filter_search = ""

process_all = False
files_to_process=[]
cmd_to_get_logs = "ls -rt "+os.path.join(apache_log_dir,ssl_error_log)+"*"
if len(sys.argv)==1:
  process_all = True
  cmd_to_get_logs = cmd_to_get_logs + " | tail -2"
  prev_hour = datetime.now()-timedelta(hours=1)
  filter_search = " | grep '"+prev_hour.strftime("^\[%a %b %d %H:[0-5][0-9]:[0-5][0-9] %Y\] ")+"'"

err, out = getstatusoutput(cmd_to_get_logs)
if err:
  print out
  sys.exit(1)
ReTime = re.compile('^\[[A-Za-z]{3} ([A-Za-z]{3} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4})\] \[[^\]]+\] \[client (.+)\]\s(.+)')
for log in out.split("\n"):
  find_cmd = "grep '%s' %s %s" % (search_for, log, filter_search)
  err, out = getstatusoutput(find_cmd)
  for line in out.split("\n"):
    m = ReTime.match(line)
    if m:
      timestamp = int(datetime.strptime(m.group(1), "%b %d %H:%M:%S %Y").strftime('%s'))*1000
      payload = {}
      payload['@timestamp'] = timestamp
      payload['ip'] = m.group(2)
      payload['message'] = line
      id = sha1(str(timestamp)  + m.group(2)).hexdigest()
      print id, payload
      send_payload("hypernews","hn-timeouts",id, dumps(payload), passwd_file="/data/es/es_secret")
