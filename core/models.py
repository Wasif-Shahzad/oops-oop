import random

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    current_level = models.IntegerField(default=1)
    current_passed = models.IntegerField(default=0)
    incorrect_counter = models.IntegerField(default=0)
    times_down = models.IntegerField(default=0)


class Question(models.Model):
    text = models.TextField()
    is_mcq = models.BooleanField(default=True)
    code = models.TextField()
    correct_answer = models.CharField(max_length=255)
    duration = models.IntegerField(default=60)

    def __str__(self):
        return f"{self.text}"


class Choice(models.Model):
    text = models.TextField()
    choice_character = models.CharField(max_length=1)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.choice_character}) {self.text}"


class Level(models.Model):
    level_number = models.IntegerField()
    questions = models.ManyToManyField(Question)

    def start(self, user, randomized=True):
        questions = list(self.questions.all())

        if randomized:
            random.shuffle(questions)

        question = questions[0] if questions else None
        return UserQuiz.objects.create(
            user=user,
            level=self,
            current_question=question,
            current_question_started_at=timezone.now()
        )


class UserQuiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    started_at = models.DateTimeField(default=timezone.now)
    current_question = models.ForeignKey(Question, null=True, on_delete=models.SET_NULL)
    current_question_started_at = models.DateTimeField(null=True)

    def submit_answer(self, answer):
        question = self.current_question
        submitted_at = timezone.now()

        timed_out = (
            submitted_at - self.current_question_started_at
        ).total_seconds() > 60

        return UserAnswer.objects.create(
            user_quiz=self,
            question=question,
            answer=answer,
            is_correct=(
                answer == question.correct_answer
                and not timed_out
            ),
            timed_out=timed_out,
            submitted_at=submitted_at
        )

    def get_next_question(self):
        answered = self.useranswer_set.values_list(
            'question_id',
            flat=True
        )

        remaining = self.level.questions.exclude(
            id__in=answered
        )

        next_question = None
        if remaining.exists():
            next_question = remaining.first()

        self.current_question = next_question
        self.current_question_started_at = (
            timezone.now() if next_question else None
        )
        self.save()
        return next_question


class UserAnswer(models.Model):
    user_quiz = models.ForeignKey(UserQuiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    answer = models.CharField()
    submitted_at = models.DateTimeField()

    is_correct = models.BooleanField()
    timed_out = models.BooleanField(default=False)
