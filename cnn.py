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

	while True:
		data = requests.get(f'https://{HOST}').text
		# flog(f'{data}')
		matches = re.findall(r"//(.*?\.[^ /\",:\?]*)", data, flags=re.RegexFlag.S | re.RegexFlag.M)
		flog(f'ret: {matches}', fprint=True)
		domains = {}
		for match in matches:
			if domains.get(match) is None:
				domains[match] = 1
			else:
				domains[match] += 1

		def take_random(elem):
			return random.randint(0, 1)

		domains = sorted(domains, key=take_random)

		for domain in domains:
			id = None
			print(f'\rconnecting to {domain} ...', end='')
			domain = re.sub(r'([^.0-9a-zA-Z])', '', domain)

			if 'cnn' not in domain:
				continue

			start = time.perf_counter_ns()
			try:
				try:
					data = requests.get(f'https://{domain}/', timeout=10)
				except Exception as e:
					print(f'exception HTTP={e}')
					continue

				content = data.text
				duration = (time.perf_counter_ns() - start) / 1000000

				# with connection:
				# cursor = connection.cursor()
				# Create a new record
				extensions = data.headers.get('x-powered-by')
				cookies = data.cookies if data.cookies else ''
				headers = "\n".join(data.headers.values())
				server = data.headers.get('server')
				code = data.status_code

				# cur = connection.cursor()
				# cur.execute(f"SELECT id FROM domains WHERE host='{domain}'")
				db.execute('SELECT id FROM domains WHERE host = %s', [domain])
				exist = db.fetchone()

				id = exist.get('id') if exist else None
				# print(f'exist: {id}')
				server = sqlescape(server) if server else ''
				cookies = ':'.join(cookies) if isinstance(cookies, requests.cookies.RequestsCookieJar) else cookies
				headers = MySQLdb.escape_string(headers) if headers else ''
				# content = connection.escape_string(content) if content else ''
				# content = "%s" % sqlescape(content)
				content = MySQLdb.escape_string(content)
				# content = sqlescape(content)
				# content = re.sub(r'([^a-z0-9 \[\]~!@#\$%\^&\*\(\)<>\'"\/]+)+', '', content)
				extensions = MySQLdb.escape_string(extensions) if extensions else ''

				# print(f'domain: [{domain}, id={id}]')

				# print(f'sql: [{sql}]')
				sql = ''
				try:
					if id is not None:
						db.execute("UPDATE domains SET host = %s, ping_ms = %s, server = %s, cookies = %s, headers = %s, content = %s, code = %s, extensions = %s WHERE id = %s",
						           [domain, str(duration), server, cookies, headers, content, str(code), extensions, str(id)])
					else:
						db.execute("INSERT INTO domains (`host`, `ping_ms`, `server`, `cookies`, `headers`, `content`, `code`, `extensions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
						           [domain, str(duration), server, cookies, headers, content, str(code), extensions])
				except Exception as e:
					print(f'\rexception sql: {e} [{db.statement}] {cnx.sql_mode}')
					flog(f'exception {e} domain:{domain}={db.statement}')
					quit()

				print(f"\r[{code}] [{domain}, id={id}]: len {len(content)}b, dur {duration}ms., redir {True if data.is_redirect else False} ")

				# connection is not autocommit by default. So you must commit to save
				# your changes.
				cnx.commit()

			except Exception as e:
				traceback.print_exc()
				type, value, traceback = sys.exc_info()
				print(f'-{value}|-{type}|-{traceback}|')
				msg = re.sub(r'([\'"])', '', str(value))
				print(f'[ ! ] {domain}: exception: {msg} [{sys.exc_info()[2]}]')
				db.execute(f"INSERT IGNORE INTO `domains` SET `error` = '{msg}', host = '{domain}'")
				# cursor = connection.cursor()
				# cursor.execute(sql)
				# cursor.close()
				# connection.commit()
				continue
			time.sleep(random.randint(1, 5))

		print(f'ok, wait ...')
		time.sleep(5)
