from django.core.management.base import BaseCommand
from core.models import Question


class Command(BaseCommand):
    help = "Remove option characters like A) , B) from text and add them as separate fields"

    def handle(self, *args, **kwargs):
        questions = Question.objects.all()
        for q in questions:
            q.correct_answer = q.correct_answer[0]
            q.save()

        self.stdout.write(
            self.style.SUCCESS("Successfully removed option characters like A) , B)")
        )
