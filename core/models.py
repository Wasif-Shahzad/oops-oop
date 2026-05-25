from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    incorrect_counter = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    question_number = models.IntegerField(default=1)


class Questions(models.Model):
    text = models.TextField()
    is_mcq = models.BooleanField(default=True)
    code = models.TextField()
    correct_answer = models.CharField(max_length=255)
    level = models.IntegerField(blank=False)

    def __str__(self):
        return f"{self.text}"


class Choices(models.Model):
    text = models.TextField()
    choice_character = models.CharField(max_length=1)
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.choice_character}) {self.text}"
