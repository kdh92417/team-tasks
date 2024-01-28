from rest_framework import status
from rest_framework.mixins import CreateModelMixin as _CreateModelMixin
from rest_framework.mixins import UpdateModelMixin as _UpdateModelMixin
from rest_framework.response import Response


class CreateModelMixin(_CreateModelMixin):
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_create_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)
        serializer = self.get_serializer(instance=create_serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_create_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        create_serializer_class = self.get_create_serializer_class()
        kwargs["context"] = self.get_serializer_context()
        return create_serializer_class(*args, **kwargs)

    def get_create_serializer_class(self):
        return (
            getattr(self, "create_serializer_class", None)
            or self.get_serializer_class()
        )


class UpdateModelMixin(_UpdateModelMixin):
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_update_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.get_serializer(instance=instance)
        return Response(serializer.data)

    def get_update_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        update_serializer_class = self.get_update_serializer_class()
        kwargs["context"] = self.get_serializer_context()
        return update_serializer_class(*args, **kwargs)

    def get_update_serializer_class(self):
        return (
            getattr(self, "update_serializer_class", None)
            or self.get_serializer_class()
        )
