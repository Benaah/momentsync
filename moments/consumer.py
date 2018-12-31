import asyncio
import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from .models import Moment
# import hashlib


class ImageUpdateConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)


        momentID = self.scope['url_route']['kwargs']['momentID']

        await self.channel_layer.group_add(
            "cool",
            self.channel_name
        )

        await self.send({
            "type": "websocket.accept"
        })

        #channel_name are UNIQUE hashes for EACH connected consumer
        # await self.send({
        #     "type": "websocket.send",
        #     "text": self.channel_name
        # })

    async def websocket_receive(self, event):
        print("receive", event)
        data = json.loads(event['text'])
        if data['type'] == "add_moment":
            # image_id_args=str(data['value']).split(".")
            # hashed_image_id = hashlib.md5(image_id_args[0].encode()).hexdigest() + "." +image_id_args[1]
            await self.channel_layer.group_send(
                "cool",
                {
                    'type': 'updateMoment',
                    'image_name': data['value']
                }
            )

    async def updateMoment(self, event):
        response = {
            "type": "add_moment",
            "value": event['image_name']
        }
        await self.send({
            "type": "websocket.send",
            "text": json.dumps(response),
        })

    async def websocket_disconnect(self, event):
        print("disconnected", event)
        await self.channel_layer.group_discard(
            "cool",
            self.channel_name
        )

    # Note when calling the below two methods, make sure to add
    # the prefix "await" to comply with async

    @database_sync_to_async
    def add_image(self, username, imageid):
        return Moment.objects.get(username=username).imgIDs.append(imageid)

    @database_sync_to_async
    def remove_image(self, username, imageid):
        return Moment.objects.get(username=username).imgIDs.remove(imageid)
