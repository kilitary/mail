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
from var_dump import var_dump
import secrets
import random
import re
import base64
from pprint import pprint, pformat
import redis
import atexit
from datetime import datetime
import traceback
import socket

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

if __name__ == '__main__':
	HOST = 'kilitary.ru'
	PORT = 25
	tot_bytes = 0

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		print(f'connecting ...')
		s.connect((HOST, PORT))
		s.sendall(b'EHLO anal\r\n')

		data = s.recv(1024)
		print(f'{data.decode("utf8")}')
		s.sendall(b'MAIL FROM:<kilitary@gmail.com> SIZE=1\r\n')
		data = s.recv(1024)
		print(f'{data.decode("utf8")}')
		s.sendall(b'RCPT TO: <kilitary@kilitary.ru>\r\n')
		data = s.recv(1024)
		print(f'{data.decode("utf8")}')
		s.sendall(b'DATA\r\n')
		data = s.recv(1024)
		print(f'{data.decode("utf8")}')
		s.setblocking(True)
		while True:
			content = b'\r\n' + (b'A' * secrets.choice(range(1, 15))) + str.encode(Randomer.str_str_generator(size=11)) + b"\r\n"
			try:
				s.sendall(content)
			except Exception as e:
				print(f'exp: {e}')

			tot_bytes += len(content)

			print(f'\r{tot_bytes / 1024.0 / 1024.0:.2f}MB ', end='')
