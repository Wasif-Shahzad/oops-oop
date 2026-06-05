from time import sleep

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import MCQForm
from .models import User, Level, Question, UserQuiz, Choice


def create_quiz(total_levels, questions_in_level, user, duration=60):
    lvls = [Level.objects.create(level_number=i+1) for i in range(total_levels)]
    for i in range(1, total_levels + 1):
        for j in range(1, questions_in_level + 1):
            lvls[i - 1].questions.add(
                Question.objects.create(
                    text=f"Question #{i}{j}",
                    is_mcq=False,
                    correct_answer=f"{i}{j}",
                    duration=duration,
                )
            )
        lvls[i - 1].save()
        lvls[i - 1].start(user, False)


class UserTest(TestCase):
    def test_user_reset(self):
        john = User.objects.create_user(
            username="john",
            current_level=5,
            times_down=3,
            incorrect_counter=1,
            current_passed=6,
        )
        john.reset()
        john.refresh_from_db()
        self.assertEqual(john.current_level, 1)
        self.assertEqual(john.times_down, 0)
        self.assertEqual(john.current_passed, 0)
        self.assertEqual(john.incorrect_counter, 0)


class QuizTest(TestCase):
    def test_level_up(self):
        """
        User's level should increase once clearing the required number of questions for a level.
        """
        with self.settings(QUIZ_NUMBER_OF_LEVELS=2, QUIZ_NUMBER_OF_QUESTIONS_IN_LEVEL=1):
            john = User.objects.create_user(username="john")
            create_quiz(2, 1, john)
            johns_quiz = UserQuiz.objects.filter(
                user=john,
                level__level_number=1,
            ).first()
            # first one is to get an initial quiz
            johns_quiz.get_next_question(randomized=False, auto_submit=False)
            johns_answer = johns_quiz.submit_answer("11")
            johns_answer.update_quiz_status()
            john.refresh_from_db()
            self.assertEqual(john.current_level, 2)

    def test_level_down(self):
        """
        User's level should decrease by one if he submits two incorrect answers.
        """
        with self.settings(QUIZ_NUMBER_OF_LEVELS=2, QUIZ_NUMBER_OF_QUESTIONS_IN_LEVEL=2):
            john = User.objects.create_user(username="john")
            create_quiz(2, 2, john)

            johns_quiz = UserQuiz.objects.filter(
                user=john,
                level__level_number=1,
            ).first()
            # first one is to get an initial quiz
            johns_quiz.get_next_question(randomized=False, auto_submit=False)
            for i in [1, 2]:
                johns_answer = johns_quiz.submit_answer(f"1{i}")
                johns_answer.update_quiz_status()
                johns_quiz.get_next_question(randomized=False)
            john.refresh_from_db()
            self.assertEqual(john.current_level, 2)

            johns_quiz = UserQuiz.objects.filter(
                user=john,
                level__level_number=2,
            ).first()
            # first one is to get an initial quiz
            johns_quiz.get_next_question(randomized=False, auto_submit=False)
            for i in range(2):
                johns_answer = johns_quiz.submit_answer(f"32")
                johns_answer.update_quiz_status()
                johns_quiz.get_next_question(randomized=False)
            john.refresh_from_db()
            self.assertEqual(john.current_level, 1)
            self.assertEqual(john.times_down, 1)

    def test_get_next_question_without_submitting(self):
        john = User.objects.create_user(username="john")
        create_quiz(1, 2, john)
        johns_quiz = UserQuiz.objects.filter(
            user=john,
            level__level_number=1
        ).first()
        # first one is to get an initial quiz
        johns_quiz.get_next_question(auto_submit=False)
        johns_quiz.get_next_question(auto_submit=True)
        john.refresh_from_db()
        self.assertEqual(john.incorrect_counter, 1)

    def test_submit_timeout(self):
        john = User.objects.create_user(username="john")
        create_quiz(1, 1, john, 2)
        johns_quiz = UserQuiz.objects.filter(
            user=john,
            level__level_number=1
        ).first()
        # first one is to get an initial quiz
        johns_quiz.get_next_question(randomized=False, auto_submit=False)
        sleep(2)
        johns_answer = johns_quiz.submit_answer("11")
        self.assertFalse(johns_answer.is_correct)
        self.assertTrue(johns_answer.timed_out)

    def test_submit_correct_in_time(self):
        john = User.objects.create_user(username="john")
        create_quiz(1, 1, john, 2)
        johns_quiz = UserQuiz.objects.filter(
            user=john,
            level__level_number=1
        ).first()
        # first one is to get an initial quiz
        johns_quiz.get_next_question(randomized=False, auto_submit=False)
        johns_answer = johns_quiz.submit_answer("11")
        self.assertTrue(johns_answer.is_correct)
        self.assertFalse(johns_answer.timed_out)

    def test_level_does_not_go_down_on_level_one_and_no_more_questions(self):
        """
        Level doesn't go down on level 1
        UserQuiz.current_question is none after all Questions in the level.
        """
        john = User.objects.create_user(username="john")
        create_quiz(1, 2, john)
        johns_quiz = UserQuiz.objects.filter(
            user=john,
            level__level_number=1
        ).first()
        # first one is to get an initial quiz
        johns_quiz.get_next_question(randomized=False, auto_submit=False)
        for i in range(2):
            johns_answer = johns_quiz.submit_answer("22")
            johns_answer.update_quiz_status()
            johns_quiz.get_next_question(randomized=False)
            john.refresh_from_db()
        self.assertEqual(john.current_level, 1)
        self.assertEqual(john.times_down, 0)
        self.assertIsNone(johns_quiz.current_question)


class ViewsTest(TestCase):
    def test_quiz_next_view_without_login(self):
        """
        Should return to home without logging in
        """
        response = self.client.get(reverse("core:next"))
        self.assertRedirects(response, reverse('core:login'))

    def test_quiz_view_without_login(self):
        """
        Should return to home without logging in
        """
        response = self.client.get(reverse("core:quiz"))
        self.assertRedirects(response, reverse('core:login'))

    def test_quiz_next_view_without_starting_quiz_and_login(self):
        """
        Should return to index
        """
        john = User.objects.create_user(username="john")
        john.set_password("john123")
        john.save()

        login_response = self.client.login(username=john.username, password="john123")
        self.assertTrue(login_response)

        response = self.client.get(reverse("core:next"))
        self.assertRedirects(response, reverse("core:index"))

    def test_quiz__view_without_starting_quiz_and_login(self):
        """
        Should return to index
        """
        john = User.objects.create_user(username="john")
        john.set_password("john123")
        john.save()

        login_response = self.client.login(username=john.username, password="john123")
        self.assertTrue(login_response)

        response = self.client.get(reverse("core:quiz"))
        self.assertRedirects(response, reverse('core:index'))

    def test_success_message(self):
        """
        User with a level higher than settings.QUIZ_NUMBER_OF_LEVELS should get success message
        """
        john = User.objects.create_user(username="john", current_level=2)
        john.set_password("john123")
        john.save()
        self.client.login(username=john.username, password="john123")

        with self.settings(QUIZ_NUMBER_OF_LEVELS=1):
            response = self.client.get(reverse('core:quiz'))
            self.assertContains(response, "Congratulations for completing the quiz!")

    def test_failure_message(self):
        """
        If there aren't any more questions we should get the Failure message.
        """
        john = User.objects.create_user(username="john")
        john.set_password("john123")
        john.save()
        self.client.login(username=john.username, password="john123")

        lvl = Level.objects.create(level_number=1)
        johns_quiz = UserQuiz.objects.create(
            user=john,
            level=lvl,
            current_question=None,
        )
        # first one is to get an initial quiz
        johns_quiz.get_next_question(randomized=False, auto_submit=False)

        response = self.client.get(reverse('core:next'))
        self.assertContains(response, "No more questions at this level. You have failed!")

    def test_submit_answer(self):
        """
        Submitting correct answer through a POST request.
        Answer should be Correct.
        """
        john = User.objects.create_user(username="john")
        john.set_password("john123")
        john.save()
        self.client.login(username=john.username, password="john123")

        q = Question.objects.create(
            text="1+1?",
            correct_answer="2",
            is_mcq=False,
        )
        lvl = Level.objects.create(level_number=1)
        lvl.questions.add(q)
        johns_quiz = UserQuiz.objects.create(
            user=john,
            level=lvl,
            current_question=q,
            current_question_started_at=timezone.now()
        )
        # first one is to get an initial quiz
        johns_quiz.get_next_question(randomized=False, auto_submit=False)

        response = self.client.post(reverse('core:quiz'), {"ans": '2'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_result"])
        self.assertTrue(response.context["answer"].is_correct)


class FormTests(TestCase):
    def test_invalid_submission_mcq_form(self):
        """
        Should return error for a non-existent option submission
        """
        question = Question.objects.create(text="question text")
        Choice.objects.bulk_create([
            Choice(
                question=question,
                text="A",
                choice_character='A',
            ),
            Choice(
                question=question,
                text="B",
                choice_character='B'
            )
        ])
        form = MCQForm({"ans": 'C'}, question=question)
        self.assertFalse(form.is_valid())
