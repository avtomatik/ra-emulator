from uuid import UUID

from app.domain.models.user import User
from app.repositories.base import InMemoryRepository


class UserRepository(InMemoryRepository[User]):
    def by_id(self, user_id: UUID) -> User | None:
        return self.find(lambda user: user.id == user_id)
