from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import django
django.setup()
from .models import *
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
# from sentence_transformers import SentenceTransformer
import os
import pickle

# Load the model and tokenizer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "spam_detector_model.h5")
TOKENIZER_PATH = os.path.join(BASE_DIR, "models", "tokenizer.pickle")

model = load_model(MODEL_PATH)

with open(TOKENIZER_PATH, 'rb') as handle:
    tokenizer = pickle.load(handle)

def predict_spam(question):
    """
    Predict if a message is spam and return the tag.
    """
    comment_seq = tokenizer.texts_to_sequences([question])
    comment_pad = pad_sequences(comment_seq, maxlen=100, padding='post')
    prediction = model.predict(comment_pad)[0][0]
    return 'Spam' if prediction > 0.5 else 'Not Spam'

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
        user = self.scope['user']
        tag = await sync_to_async(predict_spam)(message)
        room = await sync_to_async(Room.objects.get)(name=self.room_name)
        await database_sync_to_async(Message.objects.create)(room=room, tag=tag, content=message, user=user)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'chat_message',
                'message' : message,
                'username' : user.username,
                'tag' : tag
            }
        )
    
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        await self.send(text_data=json.dumps({
            'message' : message,
            'username' : username,
            'tag': event['tag']
        }))

class PollConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"room_{self.room_id}"

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_poll(self, event):
        # Get poll data from the event
        poll = event['poll']

        # Send poll data to WebSocket clients
        await self.send(text_data=json.dumps({
            "poll": poll
        }))

    async def receive(self, text_data):
        import json
        data = json.loads(text_data)

        if data['type'] == 'submit_poll_response':
            poll_id = data['poll_id']
            selected_option = data['selected_option']
            user_id = self.scope['user'].id

            # Use sync_to_asyncto interact with the database
            poll = await sync_to_async(Poll.objects.get)(id=poll_id)
            user = await sync_to_async(User.objects.get)(id=user_id)

            # Validate and save response
            is_correct = poll.correct_answer == selected_option
            await sync_to_async(PollResponse.objects.create)(
                poll=poll,
                student=user,
                selected_option=selected_option,
                is_correct=is_correct
            )

            # Broadcast response to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'poll_response',
                    'user': user,
                    'selected_option': selected_option,
                    'is_correct': is_correct
                }
            )

    async def poll_response(self, event):
        # Send the poll response to WebSocket clients
        await self.send(text_data=json.dumps({
            'type': 'poll_response',
            'user': event['user'].id,
            'selected_option': event['selected_option'],
            'is_correct': event['is_correct']
        }))