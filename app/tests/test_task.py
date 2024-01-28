import random

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from app.constants.task import TEAM_NAMES
from app.models import User, Team, Task, SubTask
from app.tests.helper import (
    fake,
    create_fake_task,
    create_fake_sub_tasks,
    create_fake_team,
    create_fake_user,
)
from scripts.create_base_data import create_team_and_user


class TaskTests(APITestCase):
    def setUp(self) -> None:
        create_team_and_user(TEAM_NAMES)

    def _test_get_tasks(
        self,
        expect_status_code: int,
        expect_task_id_list: list = None,
        user: User = None,
    ):
        if user:
            self.client.force_authenticate(user=user)
        resp = self.client.get(reverse("task-list"), HTTP_ACCEPT="application/json")

        self.assertEqual(resp.status_code, expect_status_code)
        resp_json = resp.json()
        if expect_status_code == status.HTTP_200_OK:
            sorted_task_id_list = [
                task["id"] for task in sorted(resp_json, key=lambda x: x["id"])
            ]
            self.assertIsNotNone(resp_json)
            self.assertEqual(sorted_task_id_list, sorted(expect_task_id_list))

    def _test_success_complete_sub_task(
        self, expected_status_code: int, sub_task_user: User, sub_task: SubTask
    ):
        self.assertFalse(sub_task.is_complete)
        self.assertIsNone(sub_task.completed_date)

        if sub_task_user:
            self.client.force_authenticate(user=sub_task_user)

        resp = self.client.post(
            reverse("task-completion", kwargs={"pk": sub_task.id}),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(expected_status_code, resp.status_code)

        if expected_status_code == status.HTTP_200_OK:
            sub_task.refresh_from_db()
            self.assertTrue(sub_task.is_complete)
            self.assertIsNotNone(sub_task.completed_date)

    def _test_delete_sub_task(
        self, expect_status_code, task_id, delete_sub_task_id, user
    ):
        self.client.force_authenticate(user=user)
        resp = self.client.delete(
            reverse(
                "sub-task-detail", kwargs={"task_id": task_id, "pk": delete_sub_task_id}
            ),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(resp.status_code, expect_status_code)

    def test_success_create_task(self):
        task_user = random.choice(User.objects.all())

        random_team_ids = random.sample(
            [team.id for team in Team.objects.all()], k=random.randint(1, 5)
        )

        create_task_data = {
            "title": fake.paragraph(nb_sentences=1),
            "content": fake.paragraph(nb_sentences=5),
            "team_ids": random_team_ids,
        }

        self.client.force_authenticate(user=task_user)
        resp = self.client.post(
            reverse("task-list"),
            HTTP_ACCEPT="application/json",
            data=create_task_data,
            format="json",
        )

        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        resp_json = resp.json()
        created_task_id = resp_json.get("id", None)
        self.assertIsNotNone(created_task_id)

        created_task = Task.objects.get(id=created_task_id)
        self.assertEqual(created_task.title, create_task_data["title"])
        self.assertEqual(created_task.content, create_task_data["content"])
        self.assertEqual(created_task.create_user, task_user)
        self.assertEqual(created_task.team, task_user.team)

        sorted_random_team_ids = sorted(random_team_ids)
        created_sub_task_ids = sorted(
            [sub_task.team_id for sub_task in created_task.sub_tasks.all()]
        )

        self.assertEqual(sorted_random_team_ids, created_sub_task_ids)

    def test_success_get_tasks_by_task_team(self):
        user = random.choice(User.objects.all())
        other_user = User.objects.exclude(team_id=user.team_id).first()

        task = create_fake_task(create_user=user)
        other_user_task = create_fake_task(create_user=other_user)

        user_sub_task_teams = random.sample(
            [team for team in Team.objects.exclude(id=other_user.team_id)],
            k=random.randint(1, 3),
        )
        user_task_team_ids = [team.id for team in user_sub_task_teams] + [user.team_id]
        other_user_sub_task_teams = random.sample(
            [team for team in Team.objects.exclude(Q(id__in=user_task_team_ids))],
            k=random.randint(1, 3),
        )

        user_sub_tasks = create_fake_sub_tasks(teams=user_sub_task_teams, task=task)
        other_user_sub_tasks = create_fake_sub_tasks(
            teams=other_user_sub_task_teams, task=other_user_task
        )

        self._test_get_tasks(
            expect_status_code=status.HTTP_200_OK,
            expect_task_id_list=[task.id],
            user=user,
        )
        for sub_task in user_sub_tasks:
            sub_task_team_user = User.objects.filter(team=sub_task.team).first()
            self._test_get_tasks(
                expect_status_code=status.HTTP_200_OK,
                expect_task_id_list=[task.id],
                user=sub_task_team_user,
            )

        self._test_get_tasks(
            expect_status_code=status.HTTP_200_OK,
            expect_task_id_list=[other_user_task.id],
            user=other_user,
        )
        for other_sub_task in other_user_sub_tasks:
            other_sub_task_team_user = User.objects.filter(
                team=other_sub_task.team
            ).first()
            self._test_get_tasks(
                expect_status_code=status.HTTP_200_OK,
                expect_task_id_list=[other_user_task.id],
                user=other_sub_task_team_user,
            )

        not_task_user_team = create_fake_team(is_verified=True)
        not_task_user, _ = create_fake_user(team=not_task_user_team)
        self._test_get_tasks(
            expect_status_code=status.HTTP_200_OK,
            expect_task_id_list=[],
            user=not_task_user,
        )

    def test_success_complete_sub_task(self):
        user = random.choice(User.objects.all())
        task = create_fake_task(create_user=user)
        sub_task_teams = random.sample(list(Team.objects.all()), k=random.randint(1, 3))

        user_sub_tasks = create_fake_sub_tasks(teams=sub_task_teams, task=task)
        complete_sub_task = random.choice(user_sub_tasks)
        sub_task_user = User.objects.filter(team=complete_sub_task.team).first()

        self._test_success_complete_sub_task(
            expected_status_code=status.HTTP_200_OK,
            sub_task_user=sub_task_user,
            sub_task=complete_sub_task,
        )

    def test_success_complete_all_tasks(self):
        user = random.choice(User.objects.all())
        task = create_fake_task(create_user=user)
        sub_task_teams = random.sample(list(Team.objects.all()), k=2)

        not_completed_sub_task, completed_sub_task = create_fake_sub_tasks(
            teams=sub_task_teams, task=task
        )
        completed_sub_task.is_complete = True
        completed_sub_task.completed_date = timezone.now()
        completed_sub_task.save()

        sub_task_user = User.objects.filter(team=not_completed_sub_task.team).first()

        self.assertFalse(task.is_complete)
        self.assertIsNone(task.completed_date)

        self._test_success_complete_sub_task(
            expected_status_code=status.HTTP_200_OK,
            sub_task_user=sub_task_user,
            sub_task=not_completed_sub_task,
        )

        task.refresh_from_db()
        self.assertTrue(task.is_complete)
        self.assertIsNotNone(task.completed_date)

    def test_fail_complete_task_by_other_team(self):
        user, other_user = random.sample(list(User.objects.all()), k=2)
        task = create_fake_task(create_user=user)
        sub_task_team = random.choice(Team.objects.all())

        user_sub_task = create_fake_sub_tasks(teams=[sub_task_team], task=task)[0]
        not_task_team_user = User.objects.exclude(team=sub_task_team).first()

        self._test_success_complete_sub_task(
            expected_status_code=status.HTTP_400_BAD_REQUEST,
            sub_task_user=not_task_team_user,
            sub_task=user_sub_task,
        )

    def test_success_modify_task(self):
        task_user = random.choice(User.objects.all())
        task = create_fake_task(create_user=task_user)

        modify_task_data = {
            "title": fake.paragraph(nb_sentences=1),
            "content": fake.paragraph(nb_sentences=5),
        }

        self.client.force_authenticate(user=task_user)
        resp = self.client.patch(
            reverse("task-detail", kwargs={"pk": task.id}),
            HTTP_ACCEPT="application/json",
            data=modify_task_data,
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(task.title, modify_task_data["title"])
        self.assertEqual(task.content, modify_task_data["content"])

    def test_success_delete_sub_task(self):
        task_user = random.choice(User.objects.all())
        task = create_fake_task(create_user=task_user)
        task_teams = random.sample(
            list(Team.objects.all()),
            k=random.randint(1, 3),
        )

        sub_tasks = create_fake_sub_tasks(teams=task_teams, task=task)
        delete_sub_task = random.choice(sub_tasks)

        self._test_delete_sub_task(
            expect_status_code=status.HTTP_204_NO_CONTENT,
            task_id=task.id,
            delete_sub_task_id=delete_sub_task.id,
            user=task_user,
        )

    def test_fail_delete_completed_sub_task(self):
        task_user = random.choice(User.objects.all())
        task = create_fake_task(create_user=task_user)
        task_teams = random.sample(
            list(Team.objects.all()),
            k=random.randint(1, 3),
        )

        sub_tasks = create_fake_sub_tasks(teams=task_teams, task=task)
        completed_sub_task = random.choice(sub_tasks)
        completed_sub_task.is_complete = True
        completed_sub_task.complete_date = timezone.now()
        completed_sub_task.save()

        self._test_delete_sub_task(
            expect_status_code=status.HTTP_400_BAD_REQUEST,
            task_id=task.id,
            delete_sub_task_id=completed_sub_task.id,
            user=task_user,
        )

    def test_fail_delete_sub_task_by_not_creator(self):
        task_user = random.choice(User.objects.all())
        not_task_user = User.objects.exclude(id=task_user.id).first()
        task = create_fake_task(create_user=task_user)
        task_teams = random.sample(
            list(Team.objects.all()),
            k=random.randint(1, 3),
        )

        sub_tasks = create_fake_sub_tasks(teams=task_teams, task=task)
        sub_task = random.choice(sub_tasks)

        self._test_delete_sub_task(
            expect_status_code=status.HTTP_403_FORBIDDEN,
            task_id=task.id,
            delete_sub_task_id=sub_task.id,
            user=not_task_user,
        )

    def test_success_add_sub_task(self):
        task_user = random.choice(User.objects.all())
        task = create_fake_task(create_user=task_user)
        task_teams = random.sample(
            list(Team.objects.all()),
            k=random.randint(1, 3),
        )
        add_team = Team.objects.exclude(id__in=[team.id for team in task_teams]).first()

        add_sub_task_data = {"task": task.id, "team": add_team.id}

        add_sub_task = SubTask.objects.filter(task=task, team=add_team).first()
        self.assertIsNone(add_sub_task)

        self.client.force_authenticate(user=task_user)
        resp = self.client.post(
            reverse(
                "sub-task-list",
                kwargs={
                    "task_id": task.id,
                },
            ),
            HTTP_ACCEPT="application/json",
            format="json",
            data=add_sub_task_data,
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        add_sub_task = SubTask.objects.filter(task=task, team=add_team).first()
        self.assertIsNotNone(add_sub_task)
