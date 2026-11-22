from app.domain.models.user import User
from app.repositories.base import SQLiteRepository


class UserRepository(SQLiteRepository[User]):
    kind = "users"
    model_type = User
