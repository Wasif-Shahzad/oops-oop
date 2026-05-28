from typing import override
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render, reverse, get_object_or_404
from django.urls import reverse_lazy

from .forms import UserRegisterForm
from .models import Level, UserQuiz

def index(request):
    if request.method == "POST":
        request.user.reset()

        for level in Level.objects.all():
            level.start(request.user)

        user_quiz = UserQuiz.objects.filter(
            user=request.user,
            level__level_number=request.user.current_level
        ).first()
        request.session['user_quiz'] = user_quiz.pk
        return redirect(reverse('core:quiz'))
    return render(request, 'core/index.html', {})

def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('core:index'))
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(form.cleaned_data['username'], form.cleaned_data['password'])
            login(request, new_user)
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


def quiz_view(request):
    user_quiz = get_object_or_404(UserQuiz, pk=request.session['user_quiz'])
    context = {
        "user_quiz": user_quiz,
    }
    return render(request, "core/quiz.html", context)
