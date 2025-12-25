from pathlib import Path

import aiofiles
from pydantic import BaseModel


class DayModel(BaseModel):
    day: int
    chatting_in_day: int
    chatting_in_session: int
    messages: list[str]

class ScenariosModel(BaseModel):
    scenarios: list[DayModel]


async def load_scenarios(file_path: Path | str) -> ScenariosModel:
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    async with aiofiles.open(path, encoding="utf-8") as f:
        content = await f.read()

    return ScenariosModel.model_validate_json(content)
