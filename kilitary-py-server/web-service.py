#!/usr/bin/env python

import asyncio
import json
import websockets
import logging

async def processConnection(websocket, path):
	print(f'connected {websocket.remote_address}:{websocket.local_address}')
	message = ''
	try:
		message = await websocket.recv()
	except Exception as e:
		print(f'exception: {e}')

	print(f"> {json.loads(message)}")
	print(f'process_message ... {path} {type(message)}')
	message = json.dumps({'fail': False, 'data': 200})
	print(f"< {message}")
	try:
		await websocket.send(message)
	except Exception as e:
		print(f'exception: {e}')

	try:
		message = await websocket.recv()
	except Exception as e:
		print(f'exception: {e}')
	print(f"> {json.loads(message)}")

	message = json.dumps({'error': False, 'id': 117})
	try:
		await websocket.send(message)
	except Exception as e:
		print(f'exception: {e}')

logger = logging.getLogger("websockets.server")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

start_server = websockets.serve(processConnection, "192.168.10.1", 18765)
print(f'we run on 192.168.10.1:18765')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
