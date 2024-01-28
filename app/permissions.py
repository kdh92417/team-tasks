from rest_framework.permissions import IsAuthenticated


class IsCreator(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
            super().has_object_permission(request, view, obj)
            and obj.task.create_user == request.user
        )
