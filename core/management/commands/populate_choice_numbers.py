from django.core.management.base import BaseCommand
from core.models import Choices


class Command(BaseCommand):
    help = "Remove option characters like A) , B) from text and add them as separate fields"

    def handle(self, *args, **kwargs):
        choices = Choices.objects.all()
        for choice in choices:
            new_text = choice.text[3:]
            option = choice.text[0]
            choice.text = new_text
            choice.choice_character = option
            choice.save()

        self.stdout.write(
            self.style.SUCCESS("Successfully removed option characters like A) , B)")
        )
