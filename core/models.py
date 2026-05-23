from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Questions(models.Model):
    text = models.TextField()
    is_mcq = models.BooleanField(default=True)
    code = models.TextField()
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.text}"


class Choices(models.Model):
    text = models.TextField()
    choice_character = models.CharField(max_length=1)
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.choice_character}) {self.text}"
