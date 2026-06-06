from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Question, Choice, Level, UserQuiz, UserAnswer


class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('current_level', 'current_passed', 'incorrect_counter', 'times_down',)}),
    )
    list_display = ['username', 'email', 'max_level', 'current_level', 'is_staff']


class ChoiceInLine(admin.StackedInline):
    model = Choice
    extra = 1


class QuestionModel(admin.ModelAdmin):
    inlines = [ChoiceInLine]


class UserQuizModel(admin.ModelAdmin):
    search_fields = ["user__username"]


class UserAnswerModel(admin.ModelAdmin):
    search_fields = ["user_quiz__user__username"]
    list_filter = ["is_correct", "timed_out"]
    list_display = ['__str__', 'user_quiz__user__username', 'is_correct', 'timed_out']


admin.site.register(User, CustomUserAdmin)
admin.site.register(Question, QuestionModel)
admin.site.register(Level)
admin.site.register(UserQuiz, UserQuizModel)
admin.site.register(UserAnswer, UserAnswerModel)
