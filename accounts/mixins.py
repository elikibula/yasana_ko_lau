from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    required_group = None

    def dispatch(self, request, *args, **kwargs):
        if not self.required_group:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.groups.filter(name=self.required_group).exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
