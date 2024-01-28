# python3 manage.py shell < ./scripts/create_base_data.py

from django.db import transaction

from app.models import Team, User
from app.constants.task import TEAM_NAMES


def create_team_and_user(team_names):
    with transaction.atomic():
        for team_name in TEAM_NAMES:
            team = Team.objects.create(team_name=team_name, is_verified=True)

            User.objects.create(
                team=team, user_name=team.team_name + "-" + "유저", password="1234"
            )


if __name__ == "__main__":
    create_team_and_user(TEAM_NAMES)
