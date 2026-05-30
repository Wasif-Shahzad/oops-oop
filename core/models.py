import random

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    current_level = models.IntegerField(default=1)
    current_passed = models.IntegerField(default=0)
    incorrect_counter = models.IntegerField(default=0)
    times_down = models.IntegerField(default=0)

    def reset(self):
        self.current_level = 1
        self.current_passed = self.incorrect_counter = self.times_down = 0
        self.save()


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

    def __str__(self):
        return f"Level: {self.level_number}"


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
        ).total_seconds() > self.current_question.duration

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
        if self.current_question.id not in answered:
            empty_answer = self.submit_answer("")
            empty_answer.update_quiz_status()

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

    def __str__(self):
        return f"Quiz started by {self.user.username} at {self.started_at} for level {self.level.level_number}"


class UserAnswer(models.Model):
    user_quiz = models.ForeignKey(UserQuiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    answer = models.CharField()
    submitted_at = models.DateTimeField()

    is_correct = models.BooleanField()
    timed_out = models.BooleanField(default=False)

    def update_quiz_status(self):
        user = self.user_quiz.user
        if self.is_correct:
            user.current_passed += 1
            user.incorrect_counter = 0
        else:
            user.incorrect_counter += 1

        # Level up.
        if user.current_passed == settings.QUIZ_NUMBER_OF_QUESTIONS_IN_LEVEL:
            user.current_level += 1
            user.current_passed = user.incorrect_counter = 0

        # Level down.
        if user.incorrect_counter == 2:
            if user.current_level > 1:
                user.current_level -= 1
                user.current_passed = user.incorrect_counter = 0
                user.times_down += 1
        user.save()

    def __str__(self):
        status = "correct" if self.is_correct else "incorrect"
        return f"Answer for {self.question.text} by {self.user_quiz.user.username} is {status}"
