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
	data = requests.get(f'https://{HOST}').text
	# flog(f'{data}')
	matches = re.findall(r"//(.*?\.[^ /\",:\?]*)", data, flags=re.RegexFlag.S | re.RegexFlag.M)
	flog(f'ret: {matches}', fprint=True)
	domains = {}
	for match in matches:
		if domains.get(match) is None:
			domains[match] = 1
		else:
			domains[match] = domains[match] + 1

	for domain in domains:
		#	flog(f'{domain}: {domains[domain]}', fprint=True)

		start = time.perf_counter_ns()
		try:
			data = requests.get(f'https://{domain}/')
			content = data.text
			duration = (time.perf_counter_ns() - start) / 1000000

			# with connection:
			cursor = connection.cursor()
			# Create a new record
			cookies = "\n".join(data.cookies)
			headers = "\n".join(data.headers.values())
			server = data.headers.get('server')
			code = data.status_code
			sql = f"INSERT INTO `domains` (`host`, `ping_ms`, `server`, `cookies`, `headers`, `content`, `code`)" \
			      f"VALUES ('{domain}', {duration}, '{server}', '{cookies}', '{headers}', '{content}', {code})"

			print(f"[{code}] {domain}: len {len(content)}b, dur {duration}ms. ")
			ret = cursor.execute(sql)
			cursor.close()

			# connection is not autocommit by default. So you must commit to save
			# your changes.
			connection.commit()

		except Exception as e:
			flog(f'exception: {e}')
			continue
