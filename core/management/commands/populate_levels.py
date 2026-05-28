from django.core.management.base import BaseCommand
from core.models import Question, Level


class Command(BaseCommand):
    help = "Used to populate levels"

    def handle(self, *args, **kwargs):
        questions = Question.objects.all()
        lvl, k = 0, 0
        lst = [1, 51, 98, 153, 213, 278, 343, 415, 500, 600, 800]
        all_levels = [Level.objects.create(level_number=i + 1) for i in range(10)]
        for i in range(1, len(questions)):
            if i == lst[k]:
                lvl += 1
                k += 1
            all_levels[k - 2].questions.add(questions[i])

        self.stdout.write(
            self.style.SUCCESS(f"Data written at {lvl} levels")
        )
