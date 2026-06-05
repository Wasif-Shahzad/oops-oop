from django.contrib import admin

from .models import User, Question, Choice, Level, UserQuiz, UserAnswer


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


admin.site.register(User)
admin.site.register(Question, QuestionModel)
admin.site.register(Level)
admin.site.register(UserQuiz, UserQuizModel)
admin.site.register(UserAnswer, UserAnswerModel)
