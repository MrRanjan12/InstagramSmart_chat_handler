from backend.models.user import User
from backend.constants import RANJAN, ASTRA


class AssistantRouter:

    @staticmethod
    def get_current_mode(user: User) -> str:
        """
        Returns the current assistant mode.
        """

        return user.current_node

    @staticmethod
    def switch_mode(user: User, new_mode: str):

        user.current_node = new_mode

        return user

    @staticmethod
    def is_ai_mode(user: User) -> bool:

        return user.current_node == ASTRA

    @staticmethod
    def is_human_mode(user: User) -> bool:

        return user.current_node == RANJAN