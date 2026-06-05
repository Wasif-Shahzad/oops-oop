from typing import Any, override

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render, reverse
from django.urls import reverse_lazy

from .forms import MCQForm, UserRegisterForm, TextForm
from .models import Level, UserQuiz


def restart(request):
    request.user.reset()
    return redirect(reverse('core:index'))


def index(request):
    if request.method == "POST":
        request.user.reset()

        # create new levels
        for level in Level.objects.all():
            level.start(request.user)

        return redirect(reverse('core:quiz'))
    return render(request, 'core/index.html', {})


def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('core:index'))
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user)
            return redirect(reverse('core:index'))
    else:
        form = UserRegisterForm()
    return render(request, 'core/login-register.html', {"form": form})


class CustomLoginView(LoginView):
    template_name = 'core/login-register.html'
    next_page = reverse_lazy('core:index')

    @override
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('core:index'))
        return super().get(request, *args, **kwargs)


def next_view(request):
    if not request.user.is_authenticated:
        return redirect(reverse('core:login'))

    user_quiz = UserQuiz.objects.filter(
        user=request.user,
        level__level_number=request.user.current_level,
    ).order_by("-started_at").first()
    if user_quiz is None:
        # only happens if the quiz hasn't started yet
        return redirect(reverse('core:index'))

    is_first = request.user.current_passed == 0 and request.user.incorrect_counter == 0
    user_quiz.get_next_question(auto_submit=not is_first)

    if user_quiz.current_question is None:
        return render(
            request,
            "core/result.html",
            {"message": "No more questions at this level. You have failed!"}
        )
    return redirect(reverse('core:quiz'))


def quiz_view(request):
    if not request.user.is_authenticated:
        return redirect(reverse('core:login'))

    if request.user.current_level > settings.QUIZ_NUMBER_OF_LEVELS:
        return render(
            request,
            "core/result.html",
            {"message": "Congratulations for completing the quiz!"}
        )
    user_quiz = UserQuiz.objects.filter(
        user=request.user,
        level__level_number=request.user.current_level,
    ).order_by("-started_at").first()
    if user_quiz is None:
        return redirect(reverse('core:index'))

    context: dict[str, Any] = {
        "user_quiz": user_quiz,
        "show_result": False,
    }

    if request.method == "POST":
        print("a post request")
        if user_quiz.current_question.is_mcq:
            form = MCQForm(request.POST, question=user_quiz.current_question)
        else:
            form = TextForm(request.POST)
        if form.is_valid():
            ans = form.cleaned_data["ans"]
            answer = user_quiz.submit_answer(ans)
            context["answer"] = answer
            context["show_result"] = True
            answer.update_quiz_status()
    else:
        if user_quiz.current_question.is_mcq:
            form = MCQForm(question=user_quiz.current_question)
        else:
            form = TextForm()

    context["form"] = form
    return render(request, "core/quiz.html", context)
