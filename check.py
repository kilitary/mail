import os
import sys
import time

import redis
from elasticsearch import Elasticsearch
import secrets
import random
from pprint import pprint

names = []
cid = ''
host = '194.143.146.214:9200'

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

def delete_indice():
	print(f'deleting old shit ...')
	es.indices.delete(index='kilitary-mail-system', ignore=[400, 404])
	exit(1)

def deb(msg, end='\n'):
	pid = os.getpid()
	msg = f'{pid:06d}/{cid}: {msg}'
	print(msg, end=end)
	flog(msg)
	sys.stdout.flush()
	sys.stderr.flush()

def flog(msg):
	with open('/var/log/system/kilitary-mail.log', 'at') as file:
		file.write(msg + '\r\n')

if __name__ == '__main__':
	data = sys.stdin.read()
	exit(0)
	cid = Randomer.str_id_generator(size=8)

	opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]

	deb(f'connecting ... {host}')

	es = Elasticsearch([host])
	r = redis.Redis(host='127.0.0.1', port=6379, db=1)

	if "-d" in opts:
		delete_indice()



	deb(f'{len(data)} bytes in\r\n--BEGIN--\r\n{data}\r\n--END--')

	with open(f'/tmp/{cid}.eml', 'w', errors='ignore') as file:
		file.write(data)

	es.cluster.health(wait_for_status='yellow', request_timeout=10)
	es.indices.create(index='kilitary-mail-system', ignore=400)

	body = {
		"mail": {
			'source': data
		},
		"meta": {
			"from"      : sys.argv[1],
			'to'        : sys.argv[2],
			"created_at": time.time(),
			"check-pid" : os.getpid(),
			"check-id"  : cid
		}

	}

	id = Randomer.str_id_generator(size=20)
	res = es.create(index="kilitary-mail-system", id=id, body=body)

	r.rpush('mail_ids', id)
	r.expire('mail_ids', 100)

	deb(f'store: {res}')

# test3
