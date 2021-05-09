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

def flog(msg, end='\r\n'):
	with open('/var/log/system/kilitary-mail-smtp.log', 'at') as file:
		file.write(f'{msg}' + end)

if __name__ == '__main__':
	host = sys.argv[1]

	flog(f'killing {host} comms ...')

	lines = subprocess.check_output([f"sockstat", "-c4"]).splitlines()
	for line in lines:
		line = line.decode('utf-8')
		if host in line:
			flog(f'found {line}')
			matches = re.findall(r"(\d+\.\d+\.\d+\.\d+):(\d+)\s+(\d+\.\d+\.\d+\.\d+):(\d+)", line, flags=re.RegexFlag.S | re.RegexFlag.M)
			src_host = matches[0][0]
			src_port = matches[0][1]
			dst_host = matches[0][2]
			dst_port = matches[0][3]

			target = f"{src_host}.{src_port} {dst_host}.{dst_port}"
			flog(f'\r\nkilling [{target}]\r\n')
			subprocess.call(f"/usr/sbin/tcpdrop {target}", shell=True)
	exit(0)
