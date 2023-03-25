#!/usr/bin/env python3

import aiohttp
import datetime
import hashlib
import json


class Todoist:
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    
    async def connect(self):
        try:
            await self.__find_shopping_list_project_id()
            await self.__update()
        except:
            self.failed = True
        else:
            self.failed = False
    

    def set_ha_shopping_list(self, path, reload):
        self.ha_shopping_list_path = path
        self.ha_shopping_list_reload = reload
    

    async def _get_request(self, endpoint: str, params: dict={}):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.todoist.com/rest/v2/" + endpoint, params=params, headers={
                "Authorization": "Bearer "+self.api_key
            }) as response:
                return await response.json()
    

    async def _post_request(self, endpoint: str, body: dict={}, decode: bool = True):
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.todoist.com/rest/v2/" + endpoint, json=body, headers={
                "Authorization": "Bearer "+self.api_key
            }) as response:
                if decode == True:
                    return await response.json()
                else:
                    return
    

    async def __find_shopping_list_project_id(self):
        self.shopping_list_id = None

        for project in await self._get_request("projects"):
            if project['name'] == "Alexa Shopping List":
                self.shopping_list_id = project['id']
                return
        
        raise Exception("Unable to find Alexa Shopping List")


    async def __update(self):
        found = []
        for item in await self._get_request("tasks", {"project_id": self.shopping_list_id}):
            found.append({
                "id": item['id'],
                "item": item['content']
            })

        self.shopping_list = found
        self.last_updated = datetime.datetime.now().astimezone()


    async def update(self):
        now = datetime.datetime.now().astimezone()
        diff = now - self.last_updated

        if diff.total_seconds() >= 60:
            await self.__update()
            return True
        else:
            return False
    

    async def get_shopping_list_items(self):
        await self.update()
        return self.shopping_list


    def get_shopping_list_hash(self):
        items_str = json.dumps(self.shopping_list)
        return hashlib.md5(str(items_str).encode("utf-8")).hexdigest()


    async def add_item(self, item):
        added = await self._post_request("tasks", {
            "project_id": self.shopping_list_id,
            "content": item
        })
        await self.__update()
    

    async def update_item(self, id, item):
        added = await self._post_request("tasks/"+str(id), {
            "content": item
        })
        await self.__update()
    

    async def complete_item(self, id):
        added = await self._post_request("tasks/"+str(id)+"/close", {}, False)
        await self.__update()
    

    async def homeassistant_shopping_list_updated(self, event):
        if event.data.get("action") == "add":
            await self.add_item(event.data.get("item")["name"])
            await self.export_shopping_list()

        if event.data.get("action") == "update":
            if event.data.get("item")["complete"] == True:
                await self.complete_item(event.data.get("item")["id"])
            else:
                await self.update_item(event.data.get("item")["id"], event.data.get("item")["name"])
            await self.export_shopping_list()

        if event.data.get("action") == "remove":
            await self.complete_item(event.data.get("item")["id"])
            await self.export_shopping_list()
    

    async def export_shopping_list(self):
        export = []
        for item in self.shopping_list:
            export.append({
                "id": item['id'],
                "name": item['item'],
                "complete": False
            })
        
        with open(self.ha_shopping_list_path, "w") as outfile:
            outfile.write(json.dumps(export, indent=4))
        
        await self.ha_shopping_list_reload()