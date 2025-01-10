from django.shortcuts import render, redirect
from .models import *
from sentence_transformers import SentenceTransformer, util
# Create your views here.
rel_model = SentenceTransformer('all-MiniLM-L6-v2') 
def index(request):
    if request.method == "POST":
        name = request.POST.get('name')
        room = Room.objects.create(name=name)
        return redirect("room_detail", room_id=room.id)
    rooms = Room.objects.all()
    return render(request, "dashboard.html", {'rooms': rooms})

def room_detail(request, room_id):
    room = Room.objects.get(id=room_id)
    messages = Message.objects.filter(room=room.id)
    return render(request, 'meeting.html', {'room': room, 'messages': messages})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Replace 'home' with your desired redirect URL name
        else:
            return render(request, 'loginpage.html', {'error': 'Invalid username or password'})
    return render(request, 'loginpage.html')

def create_room(request):
    if request.method == 'POST':
        title = request.POST['title']
        text = request.POST['text']
        name = title.replace(' ', '_')
        room = Room.objects.create(name=name, text=text, title=title)
        return redirect("room_detail", room_id=room.id)
    return render(request, "room_form.html")

def calculate_relevancy(content, questions, messages):
    content_embedding = rel_model.encode(content, convert_to_tensor=True)
    question_embeddings = rel_model.encode(questions, convert_to_tensor=True)

    # Calculate cosine similarity
    relevancy_scores = util.pytorch_cos_sim(content_embedding, question_embeddings)

    scores = relevancy_scores.squeeze().tolist()
    results = [(questions[i], scores[i], messages[i].user.username) for i in range(len(questions))]
    print(results)
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def dashboard(request, room_id):
    room = Room.objects.get(id=room_id)
    messages = Message.objects.filter(room=room, tag="Not Spam")
    # print(room, messages)
    not_spam_questions = []
    for i in messages:
        not_spam_questions.append(i.content)
    rel_results = calculate_relevancy(room.text, not_spam_questions, messages)
    # print(rel_results)
    return render(request, "questdash.html", {'most_relevant' : rel_results[1:15], "other_relevant" : rel_results[15: ]})

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import Poll, Room
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@login_required
def create_poll(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if room.creator != request.user:
        return HttpResponseForbidden("You are not the owner of this room and cannot create a poll.")

    if request.method == 'POST':
        question = request.POST['question']
        options = json.loads(request.POST['options'])  # {"Option 1": False, "Option 2": True}
        correct_answer = request.POST['correct_answer']

        # Create and save the poll
        poll = Poll.objects.create(
            room=room,
            question=question,
            options=options,
            correct_answer=correct_answer
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"room_{room_id}",
            {
                "type": "send_poll",
                "poll": {
                    "id": poll.id,
                    "question": poll.question,
                    "options": poll.options,
                    "created_at": str(poll.created_at)
                }
            }
        )

        # Broadcast poll to all room participants via WebSocket
        # Assuming you have a WebSocket consumer set up
        # Use Channels to send the poll to all connected users in the room

        return redirect('room_detail', room_id=room.id)
    
    return render(request, 'create_poll.html', {'room': room})