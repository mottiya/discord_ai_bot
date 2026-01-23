from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.resources_manager import Identity, ModelPromts, load_model


@pytest.fixture
def valid_prompts_yaml(tmp_path: Path) -> Path:
    data = {
        "identities": {
            123456789: {
                "name": "TestUser1",
                "init_message": "Привет!",
                "system_message": "Ты дружелюбный бот.",
                "system_prompt": "Отвечай кратко.",
            },
            987654321: {
                "name": "TestUser2",
                "system_message": "Ты второй бот.",
                "system_prompt": "Будь вежлив.",
            },
        }
    }
    file_path = tmp_path / "test_prompts.yaml"
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
    return file_path


@pytest.fixture
def invalid_prompts_yaml(tmp_path: Path) -> Path:
    data = {
        "identities": {
            "invalid_id": {
                "name": "TestUser",
                "system_message": "Сообщение",
                "system_prompt": "Промпт",
            }
        }
    }
    file_path = tmp_path / "invalid_prompts.yaml"
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
    return file_path


@pytest.fixture
def malformed_yaml(tmp_path: Path) -> Path:
    file_path = tmp_path / "malformed.yaml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{ invalid: yaml: content")
    return file_path


@pytest.mark.asyncio
async def test_load_model_success(valid_prompts_yaml: Path):
    result = await load_model(ModelPromts, valid_prompts_yaml)

    assert isinstance(result, ModelPromts)
    assert len(result.identities) == 2
    assert 123456789 in result.identities
    assert 987654321 in result.identities

    identity1 = result.identities[123456789]
    assert isinstance(identity1, Identity)
    assert identity1.name == "TestUser1"
    assert identity1.init_message == "Привет!"
    assert identity1.system_message == "Ты дружелюбный бот."

    identity2 = result.identities[987654321]
    assert identity2.init_message is None


@pytest.mark.asyncio
async def test_load_model_file_not_found():
    non_existent_path = Path("/non/existent/path/prompts.yaml")

    with pytest.raises(FileNotFoundError, match="File not found"):
        await load_model(ModelPromts, non_existent_path)


@pytest.mark.asyncio
async def test_load_model_with_string_path(valid_prompts_yaml: Path):
    result = await load_model(ModelPromts, str(valid_prompts_yaml))

    assert isinstance(result, ModelPromts)
    assert len(result.identities) == 2


@pytest.mark.asyncio
async def test_load_model_invalid_data(invalid_prompts_yaml: Path):
    with pytest.raises(ValidationError):
        await load_model(ModelPromts, invalid_prompts_yaml)


@pytest.mark.asyncio
async def test_load_model_malformed_yaml(malformed_yaml: Path):
    with pytest.raises((yaml.YAMLError, ValidationError)):
        await load_model(ModelPromts, malformed_yaml)


@pytest.mark.asyncio
async def test_load_model_empty_file(tmp_path: Path):
    empty_file = tmp_path / "empty.yaml"
    empty_file.touch()

    with pytest.raises((ValidationError, AttributeError)):
        await load_model(ModelPromts, empty_file)


def test_identy_model_validation():
    valid_identity = Identity(
        name="TestUser",
        system_message="Сообщение",
        system_prompt="Промпт",
    )

    assert valid_identity.name == "TestUser"
    assert valid_identity.init_message is None

    with pytest.raises(ValidationError):
        Identity(
            name="TestUser",
            system_prompt="Промпт",
        )


def test_model_promts_validation():
    identity1 = Identity(
        name="User1",
        system_message="Сообщение 1",
        system_prompt="Промпт 1",
    )
    identity2 = Identity(
        name="User2",
        init_message="Привет!",
        system_message="Сообщение 2",
        system_prompt="Промпт 2",
    )

    promts = ModelPromts(identities={123: identity1, 456: identity2})

    assert len(promts.identities) == 2
    assert promts.identities[123].name == "User1"
    assert promts.identities[456].init_message == "Привет!"
