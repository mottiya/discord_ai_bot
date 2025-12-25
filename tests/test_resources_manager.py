import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.resources_manager import DayModel, ScenariosModel, load_scenarios


@pytest.fixture
def valid_prompts_json(tmp_path: Path) -> Path:
    """Создаёт временный JSON файл с валидной структурой промптов."""
    data = {
        "scenarios": [
            {
                "day": 1,
                "chatting_in_day": 3,
                "chatting_in_session": 5,
                "messages": [
                    "Привет! Как дела?",
                    "Отлично, спасибо!",
                    "Хорошо, тогда договорились!",
                ],
            },
            {
                "day": 2,
                "chatting_in_day": 2,
                "chatting_in_session": 3,
                "messages": [
                    "Доброе утро!",
                    "Доброе утро! Как спалось?",
                    "Спасибо, хорошо!",
                ],
            },
        ]
    }

    file_path = tmp_path / "test_prompts.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return file_path


@pytest.fixture
def invalid_prompts_json(tmp_path: Path) -> Path:
    """Создаёт временный JSON файл с невалидной структурой."""
    data = {
        "scenarios": [
            {
                "day": "invalid",  # Должно быть int
                "chatting_in_day": 3,
                "chatting_in_session": 5,
                "messages": [],
            }
        ]
    }

    file_path = tmp_path / "invalid_prompts.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return file_path


@pytest.fixture
def malformed_json(tmp_path: Path) -> Path:
    """Создаёт временный файл с невалидным JSON."""
    file_path = tmp_path / "malformed.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json }")

    return file_path


@pytest.mark.asyncio
async def test_load_prompts_success(valid_prompts_json: Path):
    """Тест успешной загрузки валидного файла промптов."""
    result = await load_scenarios(valid_prompts_json)

    assert isinstance(result, ScenariosModel)
    assert isinstance(result.scenarios, list)
    assert len(result.scenarios) == 2

    day1 = result.scenarios[0]
    assert isinstance(day1, DayModel)
    assert day1.day == 1
    assert day1.chatting_in_day == 3
    assert day1.chatting_in_session == 5
    assert len(day1.messages) == 3
    assert day1.messages[0] == "Привет! Как дела?"

    day2 = result.scenarios[1]
    assert isinstance(day2, DayModel)
    assert day2.day == 2
    assert day2.chatting_in_day == 2
    assert day2.chatting_in_session == 3


@pytest.mark.asyncio
async def test_load_prompts_file_not_found():
    """Тест ошибки при отсутствии файла."""
    non_existent_path = Path("/non/existent/path/prompts.json")

    with pytest.raises(FileNotFoundError, match="File not found"):
        await load_scenarios(non_existent_path)


@pytest.mark.asyncio
async def test_load_prompts_with_string_path(valid_prompts_json: Path):
    """Тест загрузки с путём в виде строки."""
    result = await load_scenarios(str(valid_prompts_json))

    assert isinstance(result, ScenariosModel)
    assert len(result.scenarios) == 2


@pytest.mark.asyncio
async def test_load_prompts_invalid_data(invalid_prompts_json: Path):
    """Тест ошибки валидации при невалидных данных."""
    with pytest.raises(ValidationError):
        await load_scenarios(invalid_prompts_json)


@pytest.mark.asyncio
async def test_load_prompts_malformed_json(malformed_json: Path):
    """Тест ошибки при невалидном JSON."""
    with pytest.raises((json.JSONDecodeError, ValidationError)):
        await load_scenarios(malformed_json)


@pytest.mark.asyncio
async def test_load_prompts_empty_file(tmp_path: Path):
    """Тест ошибки при пустом файле."""
    empty_file = tmp_path / "empty.json"
    empty_file.touch()

    with pytest.raises((json.JSONDecodeError, ValidationError)):
        await load_scenarios(empty_file)


@pytest.mark.asyncio
async def test_day_model_validation():
    """Тест валидации модели DayModel."""
    valid_day = DayModel(
        day=1,
        chatting_in_day=3,
        chatting_in_session=5,
        messages=["Сообщение 1", "Сообщение 2"],
    )

    assert valid_day.day == 1
    assert valid_day.chatting_in_day == 3
    assert valid_day.chatting_in_session == 5
    assert len(valid_day.messages) == 2

    with pytest.raises(ValidationError):
        DayModel(
            day="invalid",
            chatting_in_day=3,
            chatting_in_session=5,
            messages=[],
        )


@pytest.mark.asyncio
async def test_scenarios_model_validation():
    """Тест валидации модели ScenariosModel."""
    day1 = DayModel(
        day=1,
        chatting_in_day=3,
        chatting_in_session=5,
        messages=["Сообщение 1"],
    )

    day2 = DayModel(
        day=2,
        chatting_in_day=2,
        chatting_in_session=3,
        messages=["Сообщение 2"],
    )

    scenarios = ScenariosModel(scenarios=[day1, day2])

    assert len(scenarios.scenarios) == 2
    assert scenarios.scenarios[0].day == 1
    assert scenarios.scenarios[1].day == 2


@pytest.mark.asyncio
async def test_load_real_prompts_file():
    """Тест загрузки реального файла resources/promts.json."""
    real_file = Path("resources/promts.json")

    if not real_file.exists():
        pytest.skip("Real prompts file not found")

    result = await load_scenarios(real_file)

    assert isinstance(result, ScenariosModel)
    assert len(result.scenarios) >= 1

    first_day = result.scenarios[0]
    assert first_day.day == 1
    assert first_day.chatting_in_day == 3
    assert first_day.chatting_in_session == 5
    assert len(first_day.messages) > 0
