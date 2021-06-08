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
	connection = pymysql.connect(host='kilitary.ru',
	                             user='cnn',
	                             password='cnn',
	                             database='cnn',
	                             cursorclass=pymysql.cursors.DictCursor)
	print(f'done')

	HOST = 'edition.cnn.com'
	PORT = 443

	random.seed()

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
			#	flog(f'{domain}: {domains[domain]}', fprint=True)
			domain = re.sub(r'([^.0-9a-zA-Z])', '', domain)

			start = time.perf_counter_ns()
			try:
				data = requests.get(f'https://{domain}/', timeout=10)
				content = data.text
				duration = (time.perf_counter_ns() - start) / 1000000

				# with connection:
				cursor = connection.cursor()
				# Create a new record
				extensions = data.headers.get('x-powered-by')
				cookies = "\n".join(data.cookies.values()) if data.cookies else ''
				headers = "\n".join(data.headers.values())
				server = data.headers.get('server')
				code = data.status_code

				cur = connection.cursor()
				cur.execute(f"SELECT id FROM domains WHERE host='{domain}'")
				id = cur.fetchone()
				id = id['id'] if id else None

				server = connection.escape_string(server) if server else ''
				cookies = connection.escape_string(cookies) if cookies else ''
				headers = connection.escape_string(headers) if headers else ''
				content = connection.escape_string(content) if content else ''
				#content = re.sub(r'([^a-z0-9 \[\]~!@#\$%\^&\*\(\)<>\'"\/]+)+', '', content)
				extensions = connection.escape_string(extensions) if extensions else ''

				if id is not None:
					sql = f"UPDATE `domains` SET `host` = '{domain}', `ping_ms` = {duration}, `server` = '{server}'," \
					      f"`cookies` = '{cookies}', `headers` = '{headers}', `content` = '{content}', `code` = {code}, `extensions` = '{extensions}'" \
					      f" WHERE id = {id}"
				else:
					sql = f"INSERT INTO `domains` (`host`, `ping_ms`, `server`, `cookies`, `headers`, `content`, `code`, `extensions`)" \
					      f"VALUES ('{domain}', {duration}, '{server}', '{cookies}', '{headers}', '{content}', {code}, '{extensions}')"

				cursor.execute(sql)
				cursor.close()

				print(f"[{code}] {domain}: len {len(content)}b, dur {duration}ms. ")

				# connection is not autocommit by default. So you must commit to save
				# your changes.
				connection.commit()

			except Exception as e:
				# traceback.print_exc()
				type, value, traceback = sys.exc_info()
				# print(f'-{value}|-{type}|-{traceback}|')
				msg = re.sub(r'([\'"])', '', str(value))
				print(f'[ ! ] {domain}: exception: {msg} [{sys.exc_info()[2]}]')
				sql = f"INSERT IGNORE INTO `domains` SET `error` = '{msg}', host = '{domain}'"
				cursor = connection.cursor()
				cursor.execute(sql)
				cursor.close()
				connection.commit()
				continue
			time.sleep(random.randint(1, 5))

		print(f'ok, wait ...')
		time.sleep(5)
