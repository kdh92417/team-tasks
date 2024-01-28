from django.db import models

from app.models.base import DateModel


class Team(DateModel):
    team_name = models.CharField("팀 이름", max_length=255, unique=True)
    is_verified = models.BooleanField("인증 여부", default=False)

    class Meta:
        verbose_name = verbose_name_plural = "팀"
