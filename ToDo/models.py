from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ToDo(models.Model):
    title = models.CharField(max_length=100)
    date_posted = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    is_checked = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    due_date_color = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title