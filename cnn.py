import os
import random
import re
import shutil
import string
import sys
import time
from os import getenv
from struct import *
import json
import itertools
import platform
import logging
import binascii
import threading
import io
import subprocess
import locale
import atexit
from elasticsearch import Elasticsearch
from var_dump import var_dump, var_export
import secrets
import random
from requests.structures import CaseInsensitiveDict
import re
from re import RegexFlag
import lzstring
import base64
from pprint import pprint, pformat
import redis
import atexit
from datetime import datetime
import traceback
from urllib import parse
from torpy.http.requests import do_request as http
import requests
import pymysql.cursors
from sqlescapy import sqlescape
from nmi_mysql import nmi_mysql
import MySQLdb
from datetime import date, datetime, timedelta
import mysql.connector
import requests.utils
import requests.cookies

HOST = 'edition.cnn.com'
PORT = 443

db_conf = {
	'host'         : 'kilitary.ru',
	'user'         : 'cnn',
	'password'     : 'cnn',
	'db'           : 'cnn',
	'port'         : 3306,
	'max_pool_size': 20  # optional, default is 10
}
log_file = 'cnn.log'
stable_domains = {}
domains = {}
hosts = {}
commited_origins = {}

class Randomer(object):
	def __init__(self):
		pass

	@staticmethod
	def str_generator() -> str:
		global names
		if len(names) == 0:
			names = open('names.txt', 'r').read().lower().split("\n")
		return secrets.choice(names) + "_" + (''.join(secrets.choice('1234567890') for _ in range(4)))

	@staticmethod
	def str_id_generator(size=6, chars="Aqwertyuiopasdfghjklzxcvbnm1234567890") -> str:
		return ''.join(secrets.choice(chars) for _ in range(size)).strip()

	@staticmethod
	def str_str_generator(size=6, chars=" Aqwertyuiopasdfghjklzxcvbnm 1234567890 ") -> str:
		y = ''
		for x in range(0, random.randint(1, 4)):
			y += ''.join(secrets.choice(chars) for _ in range(size)).strip()
		return y.strip()

	@staticmethod
	def rnd_name() -> str:
		global names
		if len(names) == 0:
			names = open('names.txt', 'r').read().lower().split("\n")
		return secrets.choice(names)

def flog(msg, fprint=False, filen='cnn.log'):
	with open(filen, 'at', errors='ignore') as file:
		if fprint:
			print(msg)
		file.write(msg + '\r\n')

def exception_handler(exctype, value, tb):
	print(f'Exception:')
	print('Type:', exctype)
	print('Value:', value)
	print('Traceback:', tb)

	if tb:
		format_exception = traceback.format_tb(tb)
		for line in format_exception:
			print(f'{repr(line)}')

def collect_domains(url):
	global stable_domains, domains, hosts

	print(f'[ * ] refreshing via {url} ...')

	try:
		data = requests.get(f'https://{url}')
		matches = re.findall(r"//(.*?\.[^ /\",:\?\$'=<>]*)", data.text, flags=re.RegexFlag.S | re.RegexFlag.M)
		print(f'{len(data.text)} bytes, {len(matches)} domains ', end='')

		for match in matches:
			if hosts.get(match) is None:
				hosts[match] = 1
				print(f' +{match} ')
			else:
				hosts[match] += 1

		def take_random(elem):
			return random.randint(0, 1)

		domains = sorted(hosts, key=take_random)

	except Exception as e:
		print(f'\r[ ! ] [{url}] exception HTTP={e}')
		return stable_domains

if __name__ == '__main__':
	sys.excepthook = exception_handler
	print(f'connecting to db ...')
	cnx = mysql.connector.connect(host='kilitary.ru', user='cnn', password='cnn', database='cnn', autocommit=True)  # , sql_mode="ANSI_QUOTES"
	db = cnx.cursor(buffered=True, dictionary=True)
	print(f'done {cnx.get_server_info()}')

	random.seed(os.getpid())

	if os.path.exists(log_file):
		os.unlink(log_file)

	possible_equals = list(itertools.permutations([':', '=', '-', ' '], 2))
	print(f'poss_equals={possible_equals}')
	equals = []
	for equal in possible_equals:
		dest_str = ''
		for sign in equal:
			dest_str += sign
		equals.append(dest_str)

	print(f'equals={equals}')

	url = 'edition.cnn.com'
	while True:
		collect_domains(url)

		try:
			url = domains[random.randint(0, len(domains) - 1)]
		except Exception as e:
			print(f'ahh, error domainsLen={len(domains)}')
			continue

		for domain in list(domains):
			domain = re.sub(r'([^\.0-9a-z"]*?)', '', domain, flags=RegexFlag.UNICODE | RegexFlag.I)

			if len(domain) >= 30:
				print(f'[ ! ] "{domain}" what??')
				continue

			print(f'\r[ ? ] "{domain}" connecting ... ', end='')

			start = time.perf_counter_ns()
			data = ''
			try:
				data = requests.get(f'https://{domain}/', timeout=10)
			except requests.exceptions.SSLError as e:
				print(f'\r[ % ] "{domain}" - ssl fail')
				continue
			except (ValueError, TypeError) as e:
				print(f'\r[ ! ] "{domain}" - missparsed')
				continue
			except requests.exceptions.ConnectionError as e:
				print(f'\r[ @ ] "{domain}" - dns fail')
				continue
			except requests.exceptions.ReadTimeout as e:
				print(f'\r[ ! ] "{domain}" - timeout')

			duration = (time.perf_counter_ns() - start) / 1000000

			extensions = data.headers.get('x-powered-by') if hasattr(data, 'headers') else ''

			cookies = data.cookies if hasattr(data, 'cookies') else ''

			server = data.headers.get('server') if (isinstance(data.headers, CaseInsensitiveDict) and hasattr(data, 'headers')) else data.headers
			code = data.status_code

			db.execute('SELECT id FROM domains WHERE host = %s', [domain])
			exist = db.fetchone()

			id = exist.get('id') if exist else None
			server = sqlescape(server) if server else ''
			cks_log = []
			for header_in, value_in in data.cookies.items():
				cks_log.append(f'{header_in}: {value_in}')
				commited_origins[header_in] = value_in

			cks_log = "\n".join(cks_log)
			hdrs = []
			for header, value in data.headers.items():
				hdrs.append(f'{header}: {value}')
			hdrs = "\n".join(hdrs)
			content = MySQLdb.escape_string(data.text.encode('utf-8'))
			content = re.sub(r'([^\x21-\x7e])', '?', str(content))
			extensions = MySQLdb.escape_string(extensions) if extensions else ''

			sql = ''
			if id is not None:
				db.execute("UPDATE domains SET host = %s, ping_ms = %s, server = %s, cookies = %s, headers = %s, content = %s, code = %s, extensions = %s WHERE id = %s",
				           [domain, str(duration), server, cks_log, hdrs, str(content), str(code), extensions, str(id)])
			else:
				db.execute("INSERT INTO domains (`host`, `ping_ms`, `server`, `cookies`, `headers`, `content`, `code`, `extensions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
				           [domain, str(duration), server, cks_log, hdrs, str(content), str(code), extensions])

			for header_in, value_in in data.cookies.items():
				# test stage
				if len(commited_origins):
					for header, value in commited_origins.items():
						if value == value_in and header_in != header and len(value) > 1:
							print(f'\r\n[-->] "{domain}" link: [{header}/{header_in}]:{value}', end='')
							flog(f'{domain}: [{header}/{header_in}]:{value}', filen='links.log')

			print(f"\r[{code}] \"{domain}\" id {'new' if id is None else id}, len {len(content)}, dur {duration:.2f}ms {', redir' if data.is_redirect else ''}, "
			      f"{len(data.cookies.items()) if len(data.cookies.items()) else 'no'} cookies ")

			skip_headers = ['Date', 'Expires', 'Last-Modified']
			for header, header_value in data.headers.items():
				if header in skip_headers:
					continue
				print(f'[ > ] {header}: {header_value}')
				header_value = header_value.replace('"', '').replace("'", '')
				root_matches = re.findall(r"(.*)[\s+;:]*?(.*?)", header_value, flags=re.RegexFlag.S | re.RegexFlag.U)
				if len(root_matches) > 0:
					root_matches.pop()
					for root_match in root_matches:
						# commited_origins[root_match[0]] = root_match[1]

						root_m = root_match[0]

						try:
							if '==' in root_m:
								decoded = base64.decodebytes(root_m).decode('utf-8', errors='ignore')
							else:
								decoded = '#notapplicable#'
						except TypeError as e:
							print(f'[ ! ] "{domain}" => {root_m} decode utf-8 fail => {e}')
							continue

						for equal in equals:
							root_m = root_m.replace(equal, '=')
						print(f'[L 1] [{root_m}] => {root_match[0]} -> {root_match[1]}')
						level_2_matches = re.findall(r"([^=,\s\*]+?)[=:]([^\s\*,=]*)", root_m, flags=re.RegexFlag.S | re.RegexFlag.U)
						if len(level_2_matches) > 0:
							# level_2_matches.pop()
							for level_2_match in level_2_matches:
								commited_origins[level_2_match[0]] = {'domain': domain, 'parent': level_2_match[1], 'root': root_m, 'utf8decoded': decoded}
								commited_origins[level_2_match[1]] = level_2_match[0]
								print(f'[L 2] [{level_2_match[0]}] => {level_2_match[0]} -> {level_2_match[1]}')

			cnx.commit()
			time.sleep(random.randint(0, 1))

			with open('origins.json', 'a') as f:
				y = json.dumps(commited_origins, sort_keys=False, indent=2)
				f.write(y)

		secs = random.randint(1, 4)
		for header, value in commited_origins.items():
			print(f'[ i ] {header}: {value}')

		print(f'\r\n[ * ] ok, wait {secs} sec(s) ...')
		time.sleep(secs)
