from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.models import Task, SubTask, Team


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = "__all__"


class CreateSubTaskSerializer(SubTaskSerializer):
    class Meta:
        model = SubTask
        fields = ["task", "team"]


class TaskSerializer(serializers.ModelSerializer):
    sub_tasks = SubTaskSerializer(label="하위 업무", many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "content",
            "team",
            "create_user",
            "is_complete",
            "completed_date",
            "sub_tasks",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context.get("request").user

        if not user.team.id:
            raise serializers.ValidationError(detail="유저-팀 정보가 존재하지 않습니다.")

        attrs["create_user"] = user
        attrs["team"] = user.team

        return attrs


class CreateTaskSerializer(TaskSerializer):
    team_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "content",
            "is_complete",
            "completed_date",
            "team_ids",
            "sub_tasks",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        team_ids = attrs["team_ids"]
        if not team_ids:
            raise ValidationError("최소한 한 팀에게 하위 업무를 부여해야 합니다.")

        if len(team_ids) != len(set(team_ids)):
            raise ValidationError("중복된 팀에게 중복으로 하위 업무를 부여할 수 없습니다.")

        return attrs

    def create(self, validated_data):
        title = validated_data["title"]
        content = validated_data["content"]
        team_ids = validated_data["team_ids"]
        create_user = self.context.get("request").user
        team = create_user.team

        with transaction.atomic():
            task = Task.objects.create(
                create_user=create_user, team=team, title=title, content=content
            )

            for team in team_ids:
                if not team.is_verified:
                    raise ValidationError("유효하지 않은 팀에게는 업무를 부여할 수 없습니다.")
                SubTask.objects.create(task=task, team=team)

        return task


class UpdateTaskSerializer(TaskSerializer):
    class Meta:
        model = Task
        fields = ["title", "content"]

    def update(self, instance, validated_data):
        updater = self.context.get("request").user
        if instance.create_user != updater:
            raise ValidationError("작성자 본인만 업무내용 수정이 가능합니다.")

        return super().update(instance, validated_data)


class CompleteSubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = "__all__"

    def update(self, instance, validated_data):
        task = instance.task
        instance.is_complete = True
        instance.completed_date = timezone.now()
        instance.save()

        if task.sub_tasks.filter(is_complete=False).count() == 0:
            task.is_complete = True
            task.completed_date = timezone.now()
            task.save()

        return instance
