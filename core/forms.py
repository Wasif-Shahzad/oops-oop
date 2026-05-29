from typing import override

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class MCQForm(forms.Form):
    ans = forms.ChoiceField(widget=forms.RadioSelect, required=True)

    @override
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super().__init__(*args, **kwargs)
        choices_tuple = [(c.choice_character, f"{c.text}") for c in question.choice_set.all()]
        self.fields['ans'].choices = choices_tuple


class TextForm(forms.Form):
    ans = forms.CharField(required=True, label='Enter the Answer')
