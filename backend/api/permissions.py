from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request: Request, view: None) -> bool:
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request: Request, view: None, obj) -> bool:
        return request.method in SAFE_METHODS or obj.author == request.user
