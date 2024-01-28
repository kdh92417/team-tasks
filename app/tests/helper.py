from collections import OrderedDict

from faker import Faker

from app.models import User, Team, Task, SubTask

locales = OrderedDict(
    [
        ("ko_KR", 1),
        ("en-US", 2),
    ]
)

fake = Faker(locales)


def create_fake_team(team_name: str = None, is_verified: bool = False):
    team = Team.objects.create(
        team_name=team_name or fake.name(), is_verified=is_verified
    )

    return team


def create_fake_user(team: Team, user_name=None, password=None) -> (User, str):
    if not password:
        password = fake.password()

    user = User.objects.create_user(
        user_name=user_name or fake.name(), password=password, team=team
    )

    return user, password


def create_fake_task(
    create_user: User = None,
    title: str = None,
    content: str = None,
    is_complete: bool = False,
    completed_date: str = None,
):
    if not create_user:
        create_user, password = create_fake_user()

    task = Task.objects.create(
        create_user=create_user,
        team=create_user.team,
        title=title or fake.paragraph(nb_sentences=1),
        content=content or fake.paragraph(nb_sentences=5),
        is_complete=is_complete,
        completed_date=completed_date,
    )

    return task


def create_fake_sub_tasks(
    teams: [Team],
    task: Task = None,
):
    sub_tasks = []
    if not task:
        task = create_fake_task()

    for team in teams:
        sub_task = SubTask.objects.create(team=team, task=task)
        sub_tasks.append(sub_task)

    return sub_tasks
