from src.resources_manager import ScenariosModel


class MessageGenerator:
    def __init__(self, scenarios: ScenariosModel):
        self.scenarios = scenarios
        self.generator = self.generator_message()

    async def generator_message(self) -> str:
        for msg in self.scenarios.scenarios[0].messages:
            yield msg

    async def get_next_message(self) -> str:
        return await anext(self.generator, None)
