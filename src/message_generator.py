from abc import ABC, abstractmethod

from src.resources_manager import ScenariosModel


class BaseMessageGenerator(ABC):
    @abstractmethod
    async def get_next_message(
        self,
        current_identity_id: int,
        opponent_message: str | None = None,
        message_count: int = 0,
    ) -> str | None:
        """
        Генерирует следующее сообщение.

        Args:
            current_identity_id: ID личности, которая должна ответить
            opponent_message: Последнее сообщение оппонента (опционально)
            message_count: Количество сообщений в текущей сессии

        Returns:
            Сгенерированное сообщение или None, если генерация завершена
        """
        pass


class JsonScenarioMessageGenerator(BaseMessageGenerator):
    def __init__(self, scenarios: ScenariosModel):
        self.scenarios = scenarios
        self.generator = self.generator_message()

    async def generator_message(self):
        for msg in self.scenarios.scenarios[0].messages:
            yield msg

    async def get_next_message(
        self,
        current_identity_id: int,
        opponent_message: str | None = None,
        message_count: int = 0,
    ) -> str | None:
        return await anext(self.generator, None)
