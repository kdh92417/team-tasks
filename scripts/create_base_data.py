# python3 manage.py shell < ./scripts/create_base_data.py

from django.db import transaction
from app.models import Team, User

TEAM_NAMES = ["단비", "다래", "블라블라", "철로", "땅이", "해태", "수피"]

with transaction.atomic():
    for team_name in TEAM_NAMES:
        team = Team.objects.create(
            team_name=team_name
        )

        User.objects.create(
            team=team,
            user_name=team.team_name + "-" + "유저",
            password="1234"
        )
