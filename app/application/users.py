from uuid import UUID

from app.api.dto.pagination import PageResult
from app.api.dto.user import UserSummaryDTO
from app.api.presenters.user import user_summaries, user_summary
from app.emulator.paginator import Paginator
from app.repositories.user import UserRepository


class UserService:
    RESOURCE = "/users"

    def __init__(self, repository: UserRepository, *, api_root: str) -> None:
        self.repository = repository
        self.endpoint = f"{api_root}{self.RESOURCE}"

    def list(
        self, *, query: str | None, page_token: str | None
    ) -> PageResult[UserSummaryDTO]:
        users = self.repository.all()
        if query:
            users = self._filter(users, query)
        page = Paginator.paginate(
            items=users, page_token=page_token, endpoint=self.endpoint
        )
        return PageResult(items=user_summaries(page.items), links=page.links)

    def get(self, user_id: UUID) -> UserSummaryDTO | None:
        user = self.repository.by_id(user_id)
        if user is None:
            return None
        return user_summary(user)

    @staticmethod
    def _filter(users, query: str):
        query = query.casefold()
        return [
            user
            for user in users
            if (query in (user.name_attributes.common_name or "").casefold())
        ]
