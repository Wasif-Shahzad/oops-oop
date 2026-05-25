from typing import override
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render, reverse
from django.urls import reverse_lazy

from .forms import UserRegisterForm

def index(request):
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
