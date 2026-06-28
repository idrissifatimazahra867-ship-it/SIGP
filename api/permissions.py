from rest_framework.permissions import BasePermission


class IsAdminRH(BasePermission):
    """Autorise uniquement les Administrateurs RH (is_admin=True)."""
    message = "Accès réservé à l'Administrateur RH."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )