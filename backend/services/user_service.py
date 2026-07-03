from sqlalchemy.orm import Session

from backend.models.user import User


class UserService:

    @staticmethod
    def get_by_instagram_id(
        db: Session,
        instagram_id: str
    ):

        return (
            db.query(User)
            .filter(
                User.Instagram_id == instagram_id
            )
            .first()
        )

    @staticmethod
    def create_user(
        db: Session,
        instagram_id: str
    ):

        user = User(
            Instagram_id=instagram_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_or_create(
        db: Session,
        instagram_id: str
    ):

        user = UserService.get_by_instagram_id(
            db,
            instagram_id
        )

        if user:
            return user

        return UserService.create_user(
            db,
            instagram_id
        )