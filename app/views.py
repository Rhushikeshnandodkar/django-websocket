from django.shortcuts import render, redirect
from .models import *
# Create your views here.
def index(request):
    if request.method == "POST":
        name = request.POST.get('name')
        room = Room.objects.create(name=name)
        return redirect("room_detail", room_id=room.id)
    rooms = Room.objects.all()
    return render(request, "create_room.html", {'rooms': rooms})

def room_detail(request, room_id):
    room = Room.objects.get(id=room_id)
    messages = Message.objects.filter(room=room.id)
    return render(request, 'room_detail.html', {'room': room, 'messages': messages})