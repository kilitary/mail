#!/usr/bin/env python
import asyncio
import json
import random

import websockets
import logging
import time
import os

message = ''

async def processConnection(websocket, path):
	print(f'connected {websocket.remote_address}:{websocket.local_address}')

	while True:
		try:
			print(f'reading {websocket.remote_address} ...')
			message = await websocket.recv()
			print(f"> {json.loads(message)}")
			id = random.randint(0, os.getpid())
			message = json.dumps({'error': False, 'pid': os.getpid(), 'sendlen': len(message), 'id': id})
			await websocket.send(message)
			print(f"< {json.loads(message)}")
		except Exception as e:
			print(f'exception1: {e}')
			return
		#print(f'sleeping ...')
		#time.sleep(1)

logger = logging.getLogger("websockets.server")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

start_server = websockets.serve(processConnection, "192.168.10.1", 18765)
print(f'we run on 192.168.10.1:18765')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
