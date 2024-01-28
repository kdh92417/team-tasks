from django.db.models import Q

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.models import Task, SubTask
from app.permissions import IsCreator
from app.serializers.task import (
    TaskSerializer,
    CreateTaskSerializer,
    CompleteSubTaskSerializer,
    SubTaskSerializer,
)

from app.view import CreateModelMixin, UpdateModelMixin


class TaskViewSet(ModelViewSet, CreateModelMixin, UpdateModelMixin):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    create_serializer_class = CreateTaskSerializer
    update_serializer_class = CreateTaskSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(
            Q(team_id=user.team_id) | Q(sub_tasks__team_id=user.team_id)
        ).distinct()

        return queryset

    @action(
        methods=["post"],
        detail=True,
        url_path="sub-tasks/completion",
        url_name="completion",
    )
    def complete_task(self, request, *args, **kwargs):
        sub_task_id = kwargs["pk"]
        sub_task = SubTask.objects.get(id=sub_task_id)

        if not sub_task:
            raise ValidationError("존재하지 않는 하위업무 입니다.")

        if request.user.team != sub_task.team:
            raise ValidationError("업무팀에 소속되지 않은 팀은 완료 처리를 할 수 없습니다.")

        sub_task_serializer = CompleteSubTaskSerializer()
        sub_task_serializer.update(sub_task, {})

        return Response({"message": "업무가 정상적으로 완료처리 되었습니다."}, status=status.HTTP_200_OK)


class SubTaskViewSet(ModelViewSet):
    permission_classes = [IsCreator]
    queryset = SubTask.objects.all()
    serializer_class = SubTaskSerializer

    def destroy(self, request, *args, **kwargs):
        sub_task = self.get_object()
        if sub_task.is_complete:
            raise ValidationError("완료된 하위업무는 삭제할 수 없습니다.")
        return super().destroy(request, *args, **kwargs)
