# myapp/management/commands/load_json_questions.py
import json
from django.core.management.base import BaseCommand
from core.models import Question, Choice


class Command(BaseCommand):
    help = 'Extracts questions, code, Choices, and level from a JSON file and loads them into the DB.'

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str, help='Path to the JSON file')

    def handle(self, *args, **kwargs):
        json_path = kwargs['json_path']

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to read JSON: {e}"))
            return

        questions_created = 0

        for item in data:
            # 1. Determine if it's an MCQ
            q_type = item.get('type', '').strip().lower()
            is_mcq = (q_type == 'mcq')

            # 2. Extract base fields including Level
            full_text = item.get('text', '').strip()
            correct_answer = item.get('correct', '').strip()
            level = item.get('level', 1)  # <--- Added level extraction here

            # Use `or []` because JSON might have `null` for non-MCQ Choices
            options_list = item.get('options') or []

            # 3. Distinguish `text` from `code`
            code_markers = ['\nclass ', '\nstruct ', '\nint ', '\nvoid ', '\n#include', '\nbool ', '\nchar ']
            has_code = any(marker in full_text for marker in code_markers)

            if has_code:
                # Split at the first newline
                parts = full_text.split('\n', 1)
                text = parts[0].strip()
                code_text = parts[1].strip() if len(parts) > 1 else ""
            else:
                text = full_text
                code_text = ""

            # 4. Save the Question to the Database
            question_obj = Question.objects.create(
                text=text,
                is_mcq=is_mcq,
                code=code_text,
                correct_answer=correct_answer,
            )

            # 5. Save the Choices referencing the newly created question
            for opt in options_list:
                Choice.objects.create(
                    question=question_obj,
                    text=opt.strip()
                )

            questions_created += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {questions_created} questions from JSON!'))