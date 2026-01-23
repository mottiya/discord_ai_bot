from pathlib import Path

import aiofiles
import yaml
from pydantic import BaseModel, Field


class Identity(BaseModel):
    name: str
    init_message: str | None = None
    system_message: str
    system_prompt: str


class ModelPromts(BaseModel):
    identities: dict[int, Identity] = Field(..., description="id пользователя в discord : его личность")


async def load_model[M: BaseModel](model: type[M], file_path: Path | str) -> M:
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    async with aiofiles.open(path, encoding="utf-8") as f:
        content = await f.read()

    data = yaml.safe_load(content)
    return model.model_validate(data)
