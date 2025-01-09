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