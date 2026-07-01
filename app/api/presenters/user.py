from app.api.dto.user import UserSummaryDTO
from app.domain.models.user import User


def user_summary(user: User) -> UserSummaryDTO:
    return UserSummaryDTO.model_validate(user, from_attributes=True)


def user_summaries(users: list[User]) -> list[UserSummaryDTO]:
    return [user_summary(user) for user in users]
