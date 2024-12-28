#!/usr/bin/env python3

import asyncio
import websockets
import json
import argparse
import shlex
import sys

# ============================================================


class WebSocketClient:

    def __init__(self):
        parser = argparse.ArgumentParser(description="Alexa shopping list sync client")
        parser.add_argument("ip", nargs='?', default="localhost", help="Sync server IP Address (localhost)")
        parser.add_argument("port", nargs='?', default="4000", help="Sync server port (4000)")
        parser.add_argument("amazon_url", nargs='?', default="amazon.co.uk", help="Amazon domain eg amazon.de (default is .co.uk)")
        args = parser.parse_args()

        connect_addr = args.ip
        connect_port = int(args.port)
        amazon_url = args.amazon_url
        
        self.uri = "ws://"+connect_addr+":"+str(connect_port)

    # ============================================================
    # Helpers


    async def _send_command(self, command, **kwargs):
        async with websockets.connect(self.uri) as websocket:
            request = {
                'command': command,
                'args': {
                    **kwargs
                }
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            return json.loads(response)
    

    def _command_successful(self, response):
        if "error" in response and response['error'] != None:
            return False
        return True
    

    def _command_result(self, response):
        if "result" in response:
            return response['result']
        return None
    

    def _command_error(self, response):
        if "error" in response:
            return response['error']
        return None
        

    # ============================================================
    # Server


    async def _check_server(self):
        print("Attempting to connect to "+self.uri)
        connected = await self._ping_server()
        if connected == False:
            print("Unable to connect")
            sys.exit()
        else:
            print("Connected successfully")
        
        print("\nChecking config")
        if await self._server_config_valid() == False:
            print("Config is invalid, performing setup...")
            await self._setup_server_config()
        else:
            print("Config is valid")
        
        print("\nChecking authentication")
        if await self._server_authenticated() == False:
            print("Server is not authenticated with Amazon, beginning login...")
            await self._setup_server_authentication()
        print("Server is authenticated")


    async def _ping_server(self):
        response = await self._send_command("ping")
        if self._command_successful(response):
            if self._command_result(response) == "pong":
                return True
        return False
    

    async def _server_config_valid(self):
        response = await self._send_command("config_valid")
        if self._command_successful(response):
            return self._command_result(response)
        return False
    

    async def _setup_server_config(self):
        if amazon_url == "":
            amazon_url = input("\nEnter the base url you use to access Amazon (amazon.co.uk): ")
            amazon_url = amazon_url.replace("https://", "")
            amazon_url = amazon_url.replace("http://", "")
            amazon_url = amazon_url.replace("www.", "")
            amazon_url = amazon_url.split("/")[0]
            amazon_url = amazon_url.lower()

        await self._cmd_config_set("amazon_url", amazon_url, False)
    

    async def _server_authenticated(self):
        response = await self._send_command("authenticated")
        if self._command_successful(response):
            return self._command_result(response)
        return False
    

    async def _setup_server_authentication(self):
        while True:
            print("\nEnter your Amazon login details")

            email = input("Email address: ")
            password = input("Password: ")

            response = await self._send_command("login", email=email, password=password)
            if self._command_successful(response):
                result = self._command_result(response)
                if result == 1:
                    # Logged in successfully
                    return True
                if result == 0:
                    # Requires MFA
                    break
                if result == -1:
                    # Invalid
                    print("\nInvalid details, please try again.")
            else:
                print("\nUNKNOWN ERROR: "+self._command_error(response))
        
        while True:
            mfa = input("\nEnter your OTP/MFA Code: ")
            response = await self._send_command("mfa", code=mfa)
            if self._command_successful(response):
                if self._command_result(response) == True:
                    return True
                print("Invalid code, please try again.")


    async def _cmd_shutdown(self):
        print("Sending shutdown signal to server ...")
        await self._send_command("shutdown")


    # ============================================================
    # Commands


    async def _cmd_config_set(self, key, value=None, announce=True):
        response = await self._send_command("config_set", key=key, value=value)
        if self._command_successful(response):
            if announce == True:
                print("Updated config item `"+key+"`")
            return self._command_result(response)
        print("FAILED to update config item `"+key+"`")
        return False
    

    async def _cmd_reset_server(self):
        confirm = input("Are you sure you want to reset the server? (y/N): ")
        if confirm in ["y", "Y"]:
            response = await self._send_command("reset")
            if self._command_successful(response):
                print("Server has been reset, re-running initial setup...")
                await self._check_server()
                return
            print("Reset failed")
        else:
            print("Reset cancelled")
    

    async def _cmd_get_shopping_list(self):
        response = await self._send_command("get_list")
        if self._command_successful(response):
            print(json.dumps(self._command_result(response)))
            return
        print("ERROR: "+self._command_error(response))
    

    async def _cmd_add_shopping_list_item(self, item):
        response = await self._send_command("add_item", item=item)
        if self._command_successful(response):
            print(json.dumps(self._command_result(response)))
            return
        print("ERROR: "+self._command_error(response))
    

    async def _cmd_update_shopping_list_item(self, old, new):
        response = await self._send_command("update_item", old=old, new=new)
        if self._command_successful(response):
            print(json.dumps(self._command_result(response)))
            return
        print("ERROR: "+self._command_error(response))
    

    async def _cmd_remove_shopping_list_item(self, item):
        response = await self._send_command("remove_item", item=item)
        if self._command_successful(response):
            print(json.dumps(self._command_result(response)))
            return
        print("ERROR: "+self._command_error(response))

    # ============================================================
    # Console


    def _validate_argument_count(self, arguments, expected_count):
        if len(arguments) != expected_count:
            print("Invalid arguments")
            return False
        return True


    async def _handle_commands(self, command, args):

        if command == "config_set":
            if self._validate_argument_count(args, 2):
                await self._cmd_config_set(args[0], args[1])
        
        if command == "list":
            await self._cmd_get_shopping_list()
        if command == "add":
            if self._validate_argument_count(args, 1):
                await self._cmd_add_shopping_list_item(args[0])
        if command == "update":
            if self._validate_argument_count(args, 2):
                await self._cmd_update_shopping_list_item(args[0], args[1])
        if command == "remove":
            if self._validate_argument_count(args, 1):
                await self._cmd_remove_shopping_list_item(args[0])
        
        if command == "reset":
            await self._cmd_reset_server()
        
        if command == "shutdown":
            await self._cmd_shutdown()
            return False

        return True


    async def run_console(self):
        print("Alexa Shopping List Sync Client Console.\n")
        await self._check_server()

        print("\nType 'help' for commands.\n")
        while True:
            cmd_input = input("> ").strip().lower()
            parts = shlex.split(cmd_input)

            command = parts[0]
            arguments = parts[1:]

            if command == "quit" or command == "exit":
                break
            
            keep_running = True
            # try:
            keep_running = await self._handle_commands(command, arguments)
            # except:
            #     print("Unknown error occurred")
            
            if keep_running == False:
                break
        
        print("\nGoodbye...")

# ============================================================


if __name__ == "__main__":
    client = WebSocketClient()
    asyncio.run(client.run_console())
