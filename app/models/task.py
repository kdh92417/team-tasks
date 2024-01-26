from django.db import models

from app.models.base import DateModel
from app.models.team import Team
from app.models.user import User


class Task(DateModel):
    create_user = models.ForeignKey(
        verbose_name="업무-유저", to=User, on_delete=models.SET_NULL, null=True, blank=True
    )
    team = models.ForeignKey(
        verbose_name="업무-팀", to=Team, on_delete=models.SET_NULL, null=True, blank=True
    )

    title = models.CharField("제목", max_length=100)
    content = models.TextField("내용")
    is_complete = models.BooleanField("완료 여부", default=False)
    completed_date = models.DateTimeField("완료 날짜", null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "업무"


class SubTask(DateModel):
    is_complete = models.BooleanField("완료 여부", default=False)
    completed_date = models.DateTimeField("완료 날짜", null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "하위 업무"


class SubTaskTeamAssociation(DateModel):
    subtask = models.ForeignKey(
        verbose_name="하위업무", to=SubTask, on_delete=models.CASCADE
    )
    team = models.ForeignKey(verbose_name="팀", to=Team, on_delete=models.CASCADE)

    class Meta:
        verbose_name = verbose_name_plural = "하위업무-팀-연관정보"
