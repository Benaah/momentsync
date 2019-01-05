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
            momentID,
            self.channel_name
        )

        await self.send({
            "type": "websocket.accept"
        })

    async def websocket_receive(self, event):
        print("receive", event)
        data = json.loads(event['text'])
        if data['type'] == "add_moment":
            momentID = self.scope['url_route']['kwargs']['momentID']
            imageid = data['value']
            await self.add_moment_to_database(momentID, imageid)
            # image_id_args=str(data['value']).split(".")
            # hashed_image_id = hashlib.md5(image_id_args[0].encode()).hexdigest() + "." +image_id_args[1]
            await self.channel_layer.group_send(
                momentID,
                {
                    'type': 'addmoment',
                    'image_name': imageid
                }
            )
        elif data['type'] == "delete_moment":
            momentID = self.scope['url_route']['kwargs']['momentID']
            imageid = data['value']
            await self.remove_moment_from_database(momentID, imageid)
            await self.channel_layer.group_send(
                momentID,
                {
                    'type': 'removemoment',
                    'image_name': imageid
                }
            )


    async def addmoment(self, event):
        response = {
            "type": "add_moment",
            "value": event['image_name']
        }
        await self.send({
            "type": "websocket.send",
            "text": json.dumps(response),
        })

    async def removemoment(self, event):
        response = {
            "type": "delete_moment",
            "value": event['image_name']
        }
        await self.send({
            "type": "websocket.send",
            "text": json.dumps(response),
        })

    async def websocket_disconnect(self, event):
        momentID = self.scope['url_route']['kwargs']['momentID']
        print("disconnected", event)
        await self.channel_layer.group_discard(
            momentID,
            self.channel_name
        )

    # Note when calling the below two methods, make sure to add
    # the prefix "await" to comply with async

    @database_sync_to_async
    def add_moment_to_database(self, momentid, imageid):
        mod = Moment.objects.get(momentID=momentid)
        mod.imgIDs.append(imageid)
        mod.save()

    @database_sync_to_async
    def remove_moment_from_database(self, momentid, imageid):
        mod = Moment.objects.get(momentID=momentid)
        print(mod.imgIDs)
        print(imageid)
        mod.imgIDs.remove(imageid)
        mod.save()
