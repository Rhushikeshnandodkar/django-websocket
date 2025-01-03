from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import django
django.setup()
from .models import *

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # create a room
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        # await self.send(text_data = json.dumps({"message" : f"you are connected to {self.room_name}"}))

        room = await sync_to_async(Room.objects.get)(name=self.room_name)
        messages = await sync_to_async(Message.objects.filter)(room=room)
        previous_messages = [{'content' : msg.content} async for msg in messages]
        print(previous_messages)
        await self.send(text_data=json.dumps({
            'previous_messages' : previous_messages
        }))
        #accept the connection

        

    async def disconnect(self, error_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("websocket disconnected")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        print(message)
        user = self.scope['user']
        room = await sync_to_async(Room.objects.get)(name=self.room_name)
        await database_sync_to_async(Message.objects.create)(room=room, content=message, user=user)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'chat_message',
                'message' : message,
                'username' : user.username
            }
        )
    
    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message' : message,
            'username' : username
        }))