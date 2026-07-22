from app.rbac.models import UserIdentityContext


def build_identity(user_id: str, role: str) -> UserIdentityContext:
    return UserIdentityContext(user_id=user_id, role=role)
