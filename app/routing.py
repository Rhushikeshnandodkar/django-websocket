from django.urls import re_path
from .consumers import ChatConsumer, PollConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/poll/(?P<room_id>\d+)/$', PollConsumer.as_asgi()),
]