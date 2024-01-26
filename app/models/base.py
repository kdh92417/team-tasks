from django.db import models


class DateModel(models.Model):
    created_at = models.DateTimeField("생성일시", auto_now_add=True)
    modified_at = models.DateTimeField("수정시간", auto_now=True)

    class Meta:
        abstract = True
