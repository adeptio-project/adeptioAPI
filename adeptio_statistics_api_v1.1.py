#!/usr/bin/env python
# By adeptio dev team
# Desc: 2018-09-01
# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from pymongo import MongoClient
import threading
import argparse
from os import curdir, sep
from time import gmtime, strftime, time, timezone
from datetime import datetime, timedelta
import json

# To create the server you should use: python adeptio_statistics_api_v1.py port & ip
# for example: python adeptio_statistics_api_v1.py --port 8080 --ip 127.0.0.1 

setting = {
	'favicon': 'https://adeptio.cc/favicon.ico',
	'last_updated': 'September 3, 2018',
	'date_format': '%Y-%m-%d',
	'timestamp': time(),
	'current_date': strftime("%Y-%m-%d", gmtime()),
	'yesterday_date':  (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d"),
	'bg_color': '#9d2768',

	'full_url': 'https://api.adeptio.cc/api/v1/',
	'url_path': '/api/v1/',
	'server': 'AdeptioWebServer 1.1',

	'data_list': ['masternode_offline', 'block_count', 'masternode_online', '24_highest_price', 'price', 'transaction_count', '24_btc_volume', 'buy_price', 'sell_price', 'peer_online', '24_lowest_price', 'coin_supply', '24_usd_volume', '24_ade_volume', 'difficulty', 'hashrate'],

	'mongodb': {
	  'host': 'localhost',
	  'port': 27017,
	  'database': 'adeptio_statistics',
	  'prefix': 'stat_'
	}
}

lang = {
	'title': 'Adeptio - Public API',
	'sub_title': 'Adeptio Public API',
	'version': 'Version v1.1',

	'title_latest_statistics': 'Now statistics',
	'title_latest_statistics_by_key': 'Specific now statistics',
	'title_date_statistics': 'Statistics for a Specific Date',
	'title_date_range_statistics': 'Statistics for a Specific Date Range',
	'title_aditional_information': 'Additional information',

	'description_latest_statistics': 'Output of latest stats in one call.',
	'description_latest_statistics_by_key': 'Output of latest specific key value in one call.',
	'description_date_statistics': 'Output of day stats in one call.',
	'description_date_range_statistics': 'Output of day-range stats in one call.',

	'endpoint_latest_statistics': '/now',
	'url_latest_statistics': setting['full_url']+'now',
	'endpoint_latest_statistics_by_key': '/now',
	'url_latest_statistics_by_key': setting['full_url']+'now?key=transaction_count',
	'endpoint_date_statistics': '/day',
	'url_date_statistics': setting['full_url']+'day?date='+setting['current_date'],
	'endpoint_date_range_statistics': '/dayRange',
	'url_date_range_statistics': setting['full_url']+'dayRange?startDate='+setting['yesterday_date']+'&endDate='+setting['current_date'],

	'endpoint': 'Endpoint',
	'parameters': 'Parameters',
	'parameter_name': 'Name',
	'parameter_type': 'Type',
	'parameter_required': 'Required',
	'parameter_description': 'Description',
	'parameter_date_format': 'string (date format '+setting['date_format']+')',
	'parameter_key_format': 'string',
	'parameter_yes': 'Yes',
	'parameter_example': 'Example: ',
	'parameter_key_example': 'You can get: '+', '.join(setting['data_list']),
	'method': 'Method',
	'method_get': 'GET',
	'description': 'Description',
	'full_example_url': 'Full example url',
	'example_response': 'Example Response',
	'example_error_response': 'Example Error Response',

	'api_url': 'Full url',
	'limits': 'Limits',
	'limits_description': 'Please limit requests to no more than 5 per minute. Data sync every 3 minutes.',
	'api_doc_last_updated': 'Documentation Last Updated',
	'misc': 'Misc',
	'misc_description': 'All \'XX:XX\' fields are UTC+'+str(timezone/-(60*60))+' time.',

	'button_additional_information': 'Additional information',
	'button_scroll_top': 'Scroll To Top',

	'error_no_data': 'No data',
	'error_date_statistics': 'No data for specific date',
	'error_date_range_statistics': 'No data for specific date range'
}

class Help():

	def only_letters(s,d):
		return str(''.join(i for i in d if i.isalpha()))

	def format_date(s,d):
		if d == 'now':
  			d = strftime("%Y-%m-%d", gmtime())
		try:
			return datetime.strptime(str(d),"%Y-%m-%d")
		except:
			return

	def get_parameters(s,p):
		if '?' in p:
			p = p.split("?")[1]
			return dict(i.split("=") for i in p.split("&") if i.count('=') == 1)

	def get_file_content(s,path):
		f = open(curdir + sep + path) 
		r = f.read()
		f.close()
		return r

	def gzipencode(s,content):
		import StringIO
		import gzip
		out = StringIO.StringIO()
		f = gzip.GzipFile(fileobj=out, mode='w', compresslevel=5)
		f.write(content)
		f.close()
		return out.getvalue()


class Headers():

 def text_header(self):
 	self.headers_plus = {}
 	self.headers_plus['Content-Type'] = 'text/html; charset=utf-8'

 def json_header(self):
 	self.headers_plus = {}
 	self.headers_plus['Content-Type'] = 'application/json'
 	self.headers_plus['Access-Control-Allow-Origin'] = '*'

 def _set_headers(self, code, message=None):
 	#content = self.gzipencode(strcontent)
	self.send_response(code, message)
	for h in self.headers_plus:
		self.send_header(h, self.headers_plus[h])
	#self.send_header("Content-length", str(len(str(content))))
	#self.send_header('Content-Encoding', 'gzip')
	self.end_headers()

 def send_success(self, content):
	self._set_headers(200)
	self.wfile.write(content)

 def page_not_exist(self):
	self.json_header()
	self._set_headers(403)

 def bad_request(self):
	self.json_header()
	self._set_headers(400, 'Bad Request: record does not exist')


class Pages():

 def f(self,f):
    return {
        'now': self.get_now_data,
        'day': self.get_day_data,
        'dayRange': self.get_day_range,
    }[f]

 def send_default_page(self):
 	content = self.default_page(self.get_parameters)
 	self.send_success(content)

 def get_page_slug(s,p):
	if setting['url_path'] in p[:8]:
		p = p.split("?")[0]
		return s.only_letters(p.split('/')[3])

 def get_page(self,f,p):
 	return self.f(f)(p)

 def default_page(self,v):
 	self.text_header()
	r = self.get_file_content('/index.html')
	for s in setting:
		if not isinstance(setting[s], dict):
			r = r.replace('#{setting.'+s+'}', str(setting[s]))
	for l in lang:
		if not isinstance(lang[l], dict):
			r = r.replace('#{lang.'+l+'}', str(lang[l]))
	return r

 def get_data(self):
 	self.json_header()
	self.db = DBData()

 def get_day_range(self,v):
 	self.get_data()
 	r = {}
	sd = self.format_date(v.get('startDate'))
	ed = self.format_date(v.get('endDate'))
	if sd and ed:
		delta = timedelta(days=1)
		while sd <= ed:
			d = self.db.get_day_data(sd)
			if d:
		   		r[sd.strftime("%Y-%m-%d")] = d
		   	sd += delta
	return self.json_response(r,False if r else lang.get('error_date_range_statistics'))

 def get_day_data(self,v):
 	self.get_data()
	r = self.db.get_day_data(self.format_date(v.get('date')))
	return self.json_response(r,False if r else lang.get('error_date_statistics'))

 def get_now_data(self,v):
 	self.get_data()
 	k = v.get('key') if v and v.get('key') in setting['data_list'] else None
	r = self.db.get_day_last_data(self.format_date('now'),k)
	return self.json_response(r,False if r else lang.get('error_no_data'))

 def get_key_value(self,v):
 	self.get_data()
	r = self.db.get_day_data(self.format_date(v.get('date')),v.get('key'))
	return self.json_response(r,False if r else lang.get('error_no_data'))

 def json_response(self, data, error = False):
 	r = {
 		"data": False,
 		"metadata": {
 			"timestamp": time(),
 			"error": error,
 		}
 	}
 	if data != None and data:
 		r['data'] = data
 	return json.dumps(r)


class DBData():
  def __init__(self):
  	self.mongodb = setting['mongodb']
  	self.client = MongoClient(self.mongodb['host'], self.mongodb['port'])
  	self.db = self.client[self.mongodb['database']]

  def set_db(self, day):
	self.id = self.format_table_name(day)
  	self.table = self.db[self.mongodb['prefix']+self.id]

  def format_table_name(self, day):
  	return day.strftime("%Y_%m_%d")

  def get_last_value(self, list):
  	k = sorted(list.iterkeys())
  	return list[k[-1]]

  def get_table_data(self, day):
  	self.set_db(day)
  	d = {}
  	if self.table.count() > 0:
  		d = self.table.find_one({'_id':self.id},{'_id':0})
  	return d

  def get_day_last_data(self, day, key = None):
  	d = self.get_table_data(day)
  	for k in d:
  		d[k] = self.get_last_value(d[k])
  	if key != None:
		return d.get(key)
	return d

  def get_day_data(self, day, key = None):
  	d = self.get_table_data(day)
  	if key != None:
		return d.get(key)
	return d


class HTTPRequestHandler(BaseHTTPRequestHandler, Help, Headers, Pages):

 def _parameters(self):
 	self.content_length = self.headers.get('Content-Length')
	self.full_slug = str(self.path)
	self.page_slug = self.get_page_slug(self.full_slug)
	self.get_parameters = self.get_parameters(self.full_slug)
	self.post_parameters = self.rfile.read(int(self.content_length)) if self.content_length != None else ''

 def version_string(self):
 	return setting['server']

 def do_HEAD(self):
    self._set_headers()

 def do_GET(self):
 	self._parameters()
	try:
		content = self.get_page(self.page_slug,self.get_parameters)
		self.send_success(content)
	except KeyError:
		self.send_default_page()
	return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	allow_reuse_address = True
 
 	def shutdown(self):
 		self.socket.close()
 		HTTPServer.shutdown(self)

class SimpleHttpServer():

	def __init__(self, ip, port):
 		self.server = ThreadedHTTPServer((ip,port), HTTPRequestHandler)
 
	def start(self):
 		self.server_thread = threading.Thread(target=self.server.serve_forever)
 		self.server_thread.daemon = True
 		self.server_thread.start()

 	def waitForThread(self):
 		self.server_thread.join()
 
	def addRecord(self, recordID, jsonEncodedRecord):
		LocalData.records[recordID] = jsonEncodedRecord
 
	def stop(self):
		self.server.shutdown()	
		self.waitForThread()

if __name__=='__main__':
	parser = argparse.ArgumentParser(description='HTTP Server')
	parser.add_argument('--port', type=int, help='Listening port for HTTP Server')
	parser.add_argument('--ip', help='HTTP Server IP')
	args = parser.parse_args()
	server = SimpleHttpServer(args.ip, args.port)
	print 'HTTP Server Running...........'
	server.start()
	server.waitForThread()
