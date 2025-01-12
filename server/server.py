#!/usr/bin/env python3

import asyncio
import websockets
import json
import signal
import os
from alexa import AlexaShoppingList
import time

clients = set()

alexa_running = False
alexa = None

# ============================================================
# Helpers


def _time_now():
    return int(time.time())

# ============================================================
# Config


def _config_path():
    return os.environ.get(
        "ASL_CONFIG_PATH", 
        os.path.dirname(os.path.realpath(__file__))
    )


def _load_config():
    global config
    if os.path.exists(os.path.join(_config_path(), 'config.json')):
        with open(os.path.join(_config_path(), 'config.json'), 'r') as file:
            config = json.load(file)
            return
    config = {}


def _save_config():
    with open(os.path.join(_config_path(), 'config.json'), 'w') as file:
        json.dump(config, file)


def _get_config_value(key, default=None):
    if key in config.keys():
        return config[key]
    return default


def _set_config_value(key, new_value=None):
    print("\nSet config value `"+key+"` = "+str(new_value))
    global config
    if new_value != None:
        config[key] = new_value
    else:
        del config[key]
    _save_config()


async def _cmd_config_valid():
    return os.path.exists(
        os.path.join(_config_path(), 'config.json')
    ), None


async def _cmd_config_set(args):
    _set_config_value(args['key'], args['value'])
    return True, None


async def _cmd_config_get(args):
    return _get_config_value(args['key']), None

# ============================================================
# Alexa


def _start_alexa():
    global alexa
    global alexa_running

    if alexa_running == False:
        alexa = AlexaShoppingList(
            _get_config_value("amazon_url", "amazon.co.uk"),
            _config_path()
        )
        alexa_running = True
    
    return alexa


def _stop_alexa():
    global alexa
    global alexa_running

    if alexa_running == True:
        del alexa
    
    alexa = None
    alexa_running = False

# ============================================================
# API


async def _cmd_reset():
    purge_files = ['config.json', 'cookies.json']
    for filename in purge_files:
        file_path = os.path.join(_config_path(), filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    _load_config()
    return True, None


async def _cmd_is_authenticated():
    recent = _get_config_value('auth_checked_time', 0)
    time_diff = _time_now() - recent

    if time_diff < 86400:
        return True, None

    instance = _start_alexa()

    if instance.requires_login() == True:
        print("\nAuthenticated: No")
        result = False, None
    else:
        print("\nAuthenticated: Yes")
        _set_config_value("auth_checked_time", _time_now())
        result = True, None
    
    _stop_alexa()
    return result


async def _cmd_login(args):
    print("\nAttempting login...")

    with open(os.path.join(_config_path(), 'cookies.json'), 'w') as file:
        json.dump(args['session'], file)

    return await _cmd_is_authenticated()


async def _cmd_get_shopping_list():
    instance = _start_alexa()
    if instance.requires_login():
        result =  None, "Not authenticated"
    else:
        result = instance.get_alexa_list(), None
    _stop_alexa()
    return result


async def _cmd_get_add_shopping_list_item(args):
    instance = _start_alexa()
    if instance.requires_login():
        result =  None, "Not authenticated"
    else:
        result = instance.add_alexa_list_item(args['item']), None
    _stop_alexa()
    return result


async def _cmd_get_update_shopping_list_item(args):
    instance = _start_alexa()
    if instance.requires_login():
        result =  None, "Not authenticated"
    else:
        result = instance.update_alexa_list_item(args['old'], args['new']), None
    _stop_alexa()
    return result


async def _cmd_get_remove_shopping_list_item(args):
    instance = _start_alexa()
    if instance.requires_login():
        result =  None, "Not authenticated"
    else:
        result = instance.remove_alexa_list_item(args['item']), None
    _stop_alexa()
    return result

# ============================================================
# Main handler


async def _route_command(command, arguments={}):

    # Config
    if command == "config_valid":
        return await _cmd_config_valid()
    if command == "config_set":
        return await _cmd_config_set(arguments)
    if command == "config_get":
        return await _cmd_config_get(arguments)
    if command == "reset":
        return await _cmd_reset()
    
    # Authentication
    if command == "authenticated":
        return await _cmd_is_authenticated()
    if command == "login":
        return await _cmd_login(arguments)
    if command == "mfa":
        return await _cmd_mfa(arguments)
    
    # Shopping list
    if command == "get_list":
        return await _cmd_get_shopping_list()
    if command == "add_item":
        return await _cmd_get_add_shopping_list_item(arguments)
    if command == "update_item":
        return await _cmd_get_update_shopping_list_item(arguments)
    if command == "remove_item":
        return await _cmd_get_remove_shopping_list_item(arguments)
    
    # Misc
    if command == "ping":
        return "pong", None
    if command == "shutdown":
        await _shutdown_server()


async def _process_command(websocket, path):
    clients.add(websocket)
    # try:
    async for message in websocket:
        # try:

        data = json.loads(message)
        command = data.get('command')
        arguments = data.get('args')

        response = {"result": None, "error": None}
        results = await _route_command(command, arguments)

        if len(results) == 2:
            response = {
                "result": results[0],
                "error": results[1]
            }
        else:
            response['error'] = 'Unknown command'

        # except json.JSONDecodeError:
        #     response = {'error': 'Invalid JSON'}
        # except:
        #     response = {'error': 'Fatal exception'}

        await websocket.send(json.dumps(response))
    # finally:
    clients.remove(websocket)

# ============================================================
# Start/Stop


async def _shutdown_server():
    for ws in clients:
        await ws.close()
    server.close()
    await server.wait_closed()


def _signal_handler(sig, frame):
    print("\nShutting down server...")
    asyncio.run(_shutdown_server())


async def main():
    _load_config()

    global server
    listen_addr = None
    listen_port = int(_get_config_value('listen_port', 4000))
    server = await websockets.serve(_process_command, listen_addr, listen_port)

    print("Alexa Shopping List server started on port "+str(listen_port))

    signal.signal(signal.SIGINT, _signal_handler)
    await server.wait_closed()

# ============================================================


if __name__ == "__main__":
    asyncio.run(main())