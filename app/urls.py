from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name="home"),
    path('room/<int:room_id>', views.room_detail, name="room_detail")

]