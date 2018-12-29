import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from .models import Moment


class ImageUpdateConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
        await self.send({
            "type": "websocket.accept"
        })

        momentID = self.scope['url_route']['kwargs']['momentID']

        #channel_name are UNIQUE hashes for EACH connected consumer
        await self.send({
            "type": "websocket.send",
            "text": self.channel_name
        })

    async def websocket_receive(self, event):
        print("receive", event)

    async def websocket_disconnect(self, event):
        print("disconnected", event)

    # Note when calling the below two methods, make sure to add
    # the prefix "await" to comply with async

    @database_sync_to_async
    def add_image(self, username, imageid):
        return Moment.objects.get(username=username).imgIDs.append(imageid)

    @database_sync_to_async
    def remove_image(self, username, imageid):
        return Moment.objects.get(username=username).imgIDs.remove(imageid)
