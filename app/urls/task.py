from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app.views.task import TaskViewSet, SubTaskViewSet

task_router = DefaultRouter()
task_router.register("tasks", TaskViewSet, basename="task")

sub_task_router = DefaultRouter()
task_router.register(
    r"tasks/(?P<task_id>.+)/sub-tasks",
    SubTaskViewSet,
    basename="sub-task",
)

urlpatterns = [path("", include(task_router.urls))]
