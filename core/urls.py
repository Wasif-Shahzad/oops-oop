from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(authentication_form=AuthenticationForm), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('quiz/next/', views.next_view, name='next'),
    path('quiz/restart/', views.restart, name='restart')
]
