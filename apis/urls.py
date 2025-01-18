from django.contrib import admin
from django.urls import path, include
from . import views
from .views import RelevancyAPIView, SpamDetectionAPIView

urlpatterns = [
    path('/relevancy', RelevancyAPIView.as_view(), name='relevancy-api'),
    path('/detect', SpamDetectionAPIView.as_view(), name='detect-spam'),


]