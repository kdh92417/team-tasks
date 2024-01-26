from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import transaction, models

from app.models.team import Team


class UserManager(BaseUserManager):
    def create_user(self, password=None, **extra_fields):
        if not password:
            raise ValueError("password is not provided")

        with transaction.atomic():
            user = self.model(**extra_fields)
            user.set_password(password)
            user.save(using=self._db)

        return user


class User(AbstractBaseUser):
    user_name = models.CharField("이름", max_length=255)
    team = models.ForeignKey(
        verbose_name="유저-팀", to=Team, on_delete=models.SET_NULL, null=True, blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "user_name"

    class Meta:
        verbose_name = verbose_name_plural = "사장님"
