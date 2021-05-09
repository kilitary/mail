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
import lzstring
import base64
from pprint import pprint, pformat
import redis
import atexit
from datetime import datetime
import traceback

ip = None
names = []
MAX_BYTES_IN = 1 * 1024 * 1024
cid = ''
host = '194.143.146.214:9200'
r = {}
verbose = False
bytes_in = 0
es = {}
elapsed = 0
connection_id = None

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

def delete_indec():
	print(f'deleting old shit ...')
	es.indices.delete(index='kilitary-mail-db', ignore=[400, 404])
	es.indices.delete(index='kilitary-mail-smtp', ignore=[400, 404])
	exit(0)

def deb(msg, end='\n'):
	pid = os.getpid()
	msg = f'{pid:06d}-{cid}: {msg}'
	print(msg, end=end)
	flog(msg)
	sys.stdout.flush()
	sys.stderr.flush()

def flog(msg, end='\r\n'):
	with open('/var/log/system/kilitary-mail-smtp.log', 'at') as file:
		file.write(f'{msg}' + end)

def store_mail(mta_id=None, rcpt=None, sender=None, message=None):
	if r.get(f'{mta_id}_done') == 1:
		flog(f'already stored')
		return

	dt = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

	dns = r.get(f'{mta_id}_dns').decode('utf-8')
	ip = r.get(f'{mta_id}_ip').decode('utf-8')

	body = {
		"mail": {
			'source': message
		},
		"meta": {
			'timestamp_ns': time.time_ns(),
			"created_at"  : dt,
			"check-pid"   : os.getpid(),
			"check-id"    : cid,
			'size_b'      : len(message),
			"mta-id"      : mta_id,
			"from"        : sender,
			"dns"         : dns,
			"ip"          : ip,
			"to"          : rcpt

		}

	}

	id = Randomer.str_id_generator(size=20)
	flog(f'\r* storing {mta_id}/{id} into db ...')

	res = es.create(index="kilitary-mail-db", id=id, body=body)
	flog(f'√ {res}')

	r.set(f'{mta_id}_done', 1)
	r.expire(f'{mta_id}_done', 1000)

def store_mail_log(messages=None):
	global connection_id, elapsed
	body = {
		'log'           : messages or '#empty',
		'mta-id'        : connection_id,
		'timestamp_ns'  : time.time_ns(),
		'time_taken_sms': time.time() - elapsed,
		'size_b'        : len(messages)
	}

	id = Randomer.str_id_generator(size=20)
	msgs_count = messages.count("\n")
	flog(f'* storing mail log (id={connection_id}. count={msgs_count}) ...')
	res = es.create(index="kilitary-mail-smtp", id=id, body=body)

	flog(f'√ mail log {res}')

def filter_dataline(parts):
	id = parts[5]
	opaque = parts[6]
	newline = parts[7]
	result = f"filter-dataline|{id}|{opaque}|{newline}"

	if newline != '.':
		pipe = r.pipeline()
		pipe.rpush(f'{id}_message', newline)
		pipe.expire(f'{id}_message', 1000)
		pipe.execute()

	# flog(f'< {result} ({id})')
	print(f'{result}', flush=True)

# flog(f'+ done write ({id})')

def filter_tx_rcpt(parts):
	id = parts[5]
	opaque = parts[6]
	rcpt = parts[8].strip()
	# result = f"filter-result|{id}|{opaque}|proceed"
	# flog(f'< {result}')
	if not len(rcpt):
		# result = f"filter-result|{id}|{opaque}|reject|no sender"
		flog(f'- rcpt: <empty>')
	else:
		flog(f'+ rcpt: {rcpt}')
	r.set(f'{id}_rcpt', rcpt)
	r.expire(f'{id}_rcpt', 1000)

# print(f'{result}', flush=True)

def filter_tx_mail(parts):
	id = parts[5]
	opaque = parts[6]
	sender = parts[8].strip()
	if not len(sender):
		# result = f"filter-result|{id}|{opaque}|reject|no sender"
		flog(f'- sender: <empty>')
	else:
		# result = f"filter-result|{id}|{opaque}|proceed"
		flog(f'+ sender: {sender}')
		r.set(f'{id}_sender', sender)
		r.expire(f'{id}_sender', 1000)

# flog(f'< {result}')
# print(f'{result}', flush=True)

def filter_non_implemented(parts):
	flog(f'< non-implemented {"".join(parts)}')

def filter_print(parts):
	pass  # flog(f'> {"|".join(parts)}')

def filter_mail_from(parts):
	id = parts[5]
	opaque = parts[6]
	sender = parts[7].strip()
	if not len(sender):
		result = f"filter-result|{id}|{opaque}|reject|554 empty sender"
		flog(f'- sender: <empty>')
	else:
		result = f"filter-result|{id}|{opaque}|proceed"
		flog(f'+ sender: {sender}')
		r.set(f'{id}_sender', sender)
		r.expire(f'{id}_sender', 1000)

	flog(f'< {result}')
	print(f'{result}', flush=True)

def filter_connect(parts):
	global connection_id, elapsed, ip

	elapsed = time.time()
	id = parts[5]
	opaque = parts[6]
	dns = parts[7]
	ip = parts[8]

	connection_id = id

	flog(f'@ internet: {dns} ({ip}, connection_id={connection_id})')

	pipe = r.pipeline()
	pipe.set(f'{id}_dns', dns)
	pipe.expire(f'{id}_dns', 1000)
	pipe.set(f'{id}_ip', ip)
	pipe.expire(f'{id}_ip', 1000)
	pipe.execute()

	result = f"filter-result|{id}|{opaque}|proceed"
	print(f'{result}', flush=True)

def filter_disconnect(parts):
	global connection_id, elapsed
	flog(f'* disconnect: {"/".join(parts)}')

	message_lines = r.lrange(f'{connection_id}_message', 0, -1)
	message_lines = [l.decode("utf-8") for l in message_lines]
	message = "\r\n".join(message_lines)

	# flog(f'full_message: \r\n{message}')

	rcpt = r.get(f'{connection_id}_rcpt') or '#unset'
	sender = r.get(f'{connection_id}_sender') or '#unset'

	sender = sender.decode('utf-8') if type(sender) is bytes else sender
	rcpt = rcpt.decode('utf-8') if type(rcpt) is bytes else rcpt

	if len(message_lines) >= 1:
		store_mail(rcpt=rcpt, sender=sender, message=message, mta_id=connection_id)

	mail_log = r.lrange(f'{connection_id}_flow', 0, -1)
	mail_log = [l.decode("utf-8") for l in mail_log]
	log = "\r\n".join(mail_log)

	if len(mail_log) >= 1:
		store_mail_log(messages=log)

	clear_flags()

	flog(f'* finished {connection_id} in {time.time() - elapsed:.1f} sec(s).')

def clear_flags():
	global verbose, bytes_in
	verbose = False
	bytes_in = 0

def atexit_handler():
	flog('* process exit')

if __name__ == '__main__':
	atexit.register(atexit_handler)

	es = Elasticsearch([host])
	r = redis.Redis(host='127.0.0.1', port=6379, db=0)

	opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
	if "-d" in opts:
		delete_indec()
		flog(f'indexes deleted')
		exit(0)

	if "-v" in opts:
		verbose = True

	registered = False

	while True:
		flog(f'* entering listen loop')

		try:
			resetting_connection = False
			cid = Randomer.str_id_generator(size=4)
			flog(f'{sys.argv[0]}#{cid} filter run {sys.argv[1]}')

			last_check = time.time()
			bytes_in = 0

			while sys.stdin.readable():
				line = sys.stdin.readline().rstrip()
				parts = line.split(sep='|')

				if len(parts) >= 4:
					event = parts[4]
				else:
					event = None

				bytes_in += len(line)

				if bytes_in >= MAX_BYTES_IN and not resetting_connection:
					flog(f'! too big message ({bytes_in / 1024.0 / 1024.0:.1f}mb received), dropping connection.')
					flog(f'! terminating connection with {ip} ...')
					ret = subprocess.call(f'/usr/local/bin/python3 /home/projects/tcpdetach.py {ip}', shell=True)
					flog(f'! terminate: {ret}')
					resetting_connection = True
					continue

				if len(line) and (event != 'data-line' or verbose):
					flog(f"\r> {line}")

				elif event == 'data-line':
					if time.time() - last_check >= 1.0:
						flog(f'{bytes_in / 1024.0:.1f}k', end='')
						last_check = time.time()
					else:
						flog(f'.', end='')
				else:
					flog(f'! lost connection to mta')
					exit(-1)

				if not registered and "ready" in line:
					state = f'register|filter|smtp-in|data-line'
					print(state, flush=True)
					state = f'register|report|smtp-in|tx-rcpt'
					print(state, flush=True)
					state = f'register|report|smtp-in|tx-mail'
					print(state, flush=True)
					state = f'register|report|smtp-in|protocol-client'
					print(state, flush=True)
					state = f'register|report|smtp-in|protocol-server'
					print(state, flush=True)
					state = f'register|filter|smtp-in|mail-from'
					print(state, flush=True)
					state = f'register|filter|smtp-in|connect'
					print(state, flush=True)
					state = f'register|report|smtp-in|link-disconnect'
					print(state, flush=True)
					# state = f'register|report|smtp-in|link-connect'
					# print(state, flush=True)

					ready = "register|ready"
					print(ready, flush=True)
					flog(f'+ sent ready state')

					registered = True
					continue

				if registered and len(line):
					filters = {
						"data-line"      : filter_dataline,
						"tx-rcpt"        : filter_tx_rcpt,
						"tx-mail"        : filter_tx_mail,
						"protocol-client": filter_print,
						"protocol-server": filter_print,
						"mail-from"      : filter_mail_from,
						'connect'        : filter_connect,
						'link-disconnect': filter_disconnect
					}

					filter = filters.get(event, lambda x: filter_non_implemented)

					if 'v3rb0s3' in line:
						verbose = True

					if len(parts) >= 6 and connection_id is not None and \
						(event == 'protocol-client' or event == 'protocol-server' or (event == 'data-line' and verbose)):
						data_line = f'{time.time_ns()} ' + (parts[7] if event == "data-line" else parts[6])

						pipe = r.pipeline()
						pipe.rpush(f'{connection_id}_flow', data_line)
						pipe.expire(f'{connection_id}_flow', 1000)
						pipe.execute()

					filter(parts)

		except Exception as e:
			formatted_lines = traceback.format_exc().splitlines()
			lines = "\n".join(formatted_lines)
			flog(f'exception: {e}\r\n-> {lines}')
