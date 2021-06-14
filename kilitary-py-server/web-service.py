#!/usr/bin/env python

import asyncio
# WS server example
import json
import websockets
import logging

async def process_message(websocket, path):
	print(f'connected')
	message = ''
	try:
		message = await websocket.recv()
	except Exception as e:
		print(f'exception: {e}')

	print(f'process_message ... {path} {type(message)}')
	message = json.dumps({'test1': 1, 'test2': 2})
	print(f"< {message}")
	try:
		await websocket.send(message)
	except Exception as e:
		print(f'exception: {e}')
	print(f"> {json.loads(message)}")

async def onConnection(websocket, path):
	print(f'connected {websocket.remote_address}')
	message = ''
	try:
		message = await websocket.recv()
	except Exception as e:
		print(f'exception: {e}')

	print(f'process_message ... {path} {type(message)}')
	message = json.dumps({'test1': 1, 'test2': 2})
	print(f"< {message}")
	try:
		await websocket.send(message)
	except Exception as e:
		print(f'exception: {e}')
	print(f"> {json.loads(message)}")

logger = logging.getLogger("websockets.server")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

start_server = websockets.serve(onConnection, "192.168.10.1", 18765)
print(f'we run')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
