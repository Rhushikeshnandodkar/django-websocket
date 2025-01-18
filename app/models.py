from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name
    
class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tag = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.content[:20]}..."
    
class Poll(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    question = models.CharField(max_length=500, null=True, blank=True)
    options = models.JSONField(null=True, blank=True)  # Example: {"Option 1": False, "Option 2": True}
    correct_answer = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

class PollResponse(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_responses')
    selected_option = models.CharField(max_length=255)  # To store the user's selected option
    is_correct = models.BooleanField()  # Indicates whether the response was correct or not
    correct_option = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)  # To track when the response was submitted

    class Meta:
        unique_together = ('poll', 'student')  # Ensure a user can respond to a poll only once
        ordering = ['-timestamp']  # Order responses by the most recent

    def __str__(self):
        return f"{self.student.username} - {self.poll.question} - {self.selected_option} - {'Correct' if self.is_correct else 'Wrong'}"


class Meeting(models.Model):
    topic = models.CharField(max_length=255)
    host_email = models.EmailField()
    start_time = models.DateTimeField()
    duration = models.IntegerField()
    meeting_id = models.CharField(max_length=255)
    join_url = models.URLField()
    start_url = models.URLField()

    def __str__(self):
        return self.topic