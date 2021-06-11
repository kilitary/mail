import os
import random
import re
import shutil
import string
import sys
import time
from os import getenv
from struct import *
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
import re
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

db_conf = {
	'host'         : 'kilitary.ru',
	'user'         : 'cnn',
	'password'     : 'cnn',
	'db'           : 'cnn',
	'port'         : 3306,
	'max_pool_size': 20  # optional, default is 10
}
log_file = 'cnn.log'

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

def flog(msg, fprint=False):
	with open('cnn.log', 'at', errors='ignore') as file:
		if fprint:
			print(msg)
		file.write(msg + '\r\n')

if __name__ == '__main__':
	print(f'connecting to db ...')
	# connection = pymysql.connect(host='kilitary.ru',
	#                              user='cnn',
	#                              password='cnn',
	#                              database='cnn',
	#                              cursorclass=pymysql.cursors.DictCursor)
	# db = nmi_mysql.DB(db_conf)
	cnx = mysql.connector.connect(host='kilitary.ru', user='cnn', password='cnn', database='cnn', autocommit=True)  # , sql_mode="ANSI_QUOTES"
	db = cnx.cursor(buffered=True, dictionary=True)
	print(f'done {cnx.get_server_info()}')

	# cursor.execute("insert into domains (host, error) values(%s, %d)", ['df', 304])
	# cnx.commit()
	# sys.exit(0)

	HOST = 'edition.cnn.com'
	PORT = 443

	random.seed()

	if os.path.exists(log_file):
		os.unlink(log_file)

	url = 'edition.cnn.com'
	domains = {}
	while True:
		print(f'refreshing via {url} ...', end='')
		try:
			data = requests.get(f'https://{url}').text
		except Exception as e:
			print(f'\r[ ! ] [{url}] exception HTTP={e}')
			url = domains[random.randint(0, len(domains) - 1)]
			print(f'next safe domain: {url}')
			continue

		# flog(f'{data}')

		matches = re.findall(r"//(.*?\.[^ /\",:\?]*)", data, flags=re.RegexFlag.S | re.RegexFlag.M)
		print(f' {len(data)} bytes, {len(matches)} domains\r')
		flog(f'ret: {matches}', fprint=True)

		for match in matches:
			if domains.get(match) is None:
				domains[match] = 1
			else:
				domains[match] += 1
			print(f'+{match} ', end='')

		if len(matches):
			print(f'\n')

		def take_random(elem):
			return random.randint(0, 1)

		domains_a = sorted(domains, key=take_random)

		for domain in domains_a:
			url = domains_a[random.randint(0, len(domains_a) - 1)]

			id = None
			print(f'\r[ ? ] connecting to {domain} ...', end='')
			domain = re.sub(r'([^.0-9a-zA-Z])', '', domain)

			# if 'cnn' not in domain:
			# 	continue

			start = time.perf_counter_ns()
			try:
				try:
					data = requests.get(f'https://{domain}/', timeout=10)
				except requests.exceptions.SSLError as e:
					print(f'\r[ % ] "{domain})" ssl fail')
					continue
				except requests.exceptions.ConnectionError as e:
					print(f'"\r[ ! ] "{domain}" - dns fail')
					continue
				except Exception as e:
					type, value, traceback = sys.exc_info()
					print(f'\r[ ! ] "{domain}" exception {type} HTTP={e}')
					continue

				content = data.text
				duration = (time.perf_counter_ns() - start) / 1000000

				# with connection:
				# cursor = connection.cursor()
				# Create a new record
				extensions = data.headers.get('x-powered-by')
				cookies = data.cookies if data.cookies else ''
				# headers = "\n".join(data.headers.values())
				server = data.headers.get('server')
				code = data.status_code

				# cur = connection.cursor()
				# cur.execute(f"SELECT id FROM domains WHERE host='{domain}'")
				db.execute('SELECT id FROM domains WHERE host = %s', [domain])
				exist = db.fetchone()

				id = exist.get('id') if exist else None
				# print(f'exist: {id}')
				server = sqlescape(server) if server else ''
				cks = []
				for header, value in data.cookies.items():
					cks.append(f'{header}: {value}')
				cks = "\n".join(cks)
				hdrs = []
				for header, value in data.headers.items():
					hdrs.append(f'{header}: {value}')
				hdrs = "\n".join(hdrs)
				# content = connection.escape_string(content) if content else ''
				# content = "%s" % sqlescape(content)
				content = MySQLdb.escape_string(content)
				content = re.sub(r'([^\x21-\x7e]*)', '', str(content))
				# content = sqlescape(content)
				# content = re.sub(r'([^a-z0-9 \[\]~!@#\$%\^&\*\(\)<>\'"\/]+)+', '', content)
				extensions = MySQLdb.escape_string(extensions) if extensions else ''

				# print(f'domain: [{domain}, id={id}]')

				# print(f'sql: [{sql}]')
				sql = ''
				try:
					if id is not None:
						db.execute("UPDATE domains SET host = %s, ping_ms = %s, server = %s, cookies = %s, headers = %s, content = %s, code = %s, extensions = %s WHERE id = %s",
						           [domain, str(duration), server, cks, hdrs, str(content), str(code), extensions, str(id)])
					else:
						db.execute("INSERT INTO domains (`host`, `ping_ms`, `server`, `cookies`, `headers`, `content`, `code`, `extensions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
						           [domain, str(duration), server, cks, hdrs, str(content), str(code), extensions])
				except Exception as e:
					print(f'\r\nexception sql: {e} [{db.statement}] {cnx.sql_mode}')
					flog(f'exception {e} domain:{domain}={db.statement}')
					quit()

				print(f"\r[{code}] \"{domain}\" id {'new' if id is None else id}, len {len(content)}, dur {duration}ms {', redir' if data.is_redirect else ''}, "
				                                         f"{len(data.cookies.items()) if len(data.cookies.items()) else 'no'} cookies ")

				# connection is not autocommit by default. So you must commit to save
				# your changes.
				cnx.commit()

			except Exception as e:
				type, value, traceback = sys.exc_info()
				print(f'\r-{value}|-{type}|-{traceback}|')
				msg = re.sub(r'([\'"])', '', str(value))
				print(f'\r[ ! ] {domain}: exception: {msg} [{sys.exc_info()[2]}]')
				db.execute(f"INSERT IGNORE INTO `domains` SET `error` = '{msg}', host = '{domain}'")
				# cursor = connection.cursor()
				# cursor.execute(sql)
				# cursor.close()
				# connection.commit()
				continue
			time.sleep(random.randint(0, 1))

		print(f'\r\nok, wait ...')
		time.sleep(random.randint(0, 4))
