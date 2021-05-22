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

def flog(msg, end='\r\n', case='smtp'):
	with open('/var/log/system/kilitary-mail-' + case + '.log', 'at') as file:
		file.write(f'{msg}' + end)

if __name__ == '__main__':
	host = sys.argv[1]

	flog(f'killing {host} comms ...', case='terminate')

	lines = subprocess.check_output([f"/usr/local/system/bin/sockstat", "-c4"]).decode('UTF-8').splitlines()
	for line in lines:
		flog(f"line [{line}]", case='terminate')
		if host in line:
			flog(f'found {line}', case='terminate')
			matches = re.findall(r"(\d+\.\d+\.\d+\.\d+):(\d+)\s+(\d+\.\d+\.\d+\.\d+):(\d+)", line, flags=re.RegexFlag.S | re.RegexFlag.M)
			flog(f'matches: {matches}')

			src_host = matches[0][0]
			src_port = matches[0][1]
			dst_host = matches[0][2]
			dst_port = matches[0][3]

			target = f"{src_host}.{src_port} {dst_host}.{dst_port}"
			flog(f'\r\nkilling [{target}]\r\n', case='terminate')
			subprocess.call(f"/usr/local/system/bin/tcpdrop {target}", shell=True)
	exit(0)
