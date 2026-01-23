import logging
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

logger = logging.getLogger("llm")


class DiscordChatMessage(BaseModel):
    content: str
    author_id: int
    author_name: str
    reply_id: int | None = None
    reply_name: str | None = None


class ValidationResponse(BaseModel):
    validation_status: Literal["reject", "approve"] = "reject"
    reject_reason: str | None = None


class IdentityState(BaseModel):
    messages: list[DiscordChatMessage]
    system_message: SystemMessage
    system_prompt: str
    discord_id: int
    discord_name: str
    main_llm: BaseChatModel
    validate_prompt: str = ""
    response_msg: AIMessage | None = None
    validation_response: ValidationResponse | None = None

    def clear(self) -> None:
        self.response_msg = None
        self.validation_response = None


def create_identity_state(
    messages: list[DiscordChatMessage],
    discord_id: int,
    system_message: str,
    system_prompt: str,
    name: str,
    llm: BaseChatModel,
) -> IdentityState:
    return IdentityState(
        messages=messages,
        system_message=SystemMessage(content=system_message),
        system_prompt=system_prompt,
        discord_id=discord_id,
        discord_name=name,
        main_llm=llm,
    )


gen_msg_prompt_template = PromptTemplate(
    template="""{system_prompt}

Твой id: {discord_id}
Твой name: {discord_name}

История чата: {history}
""",
    input_variables=["system_prompt", "discord_id", "discord_name", "history"],
)

validation_prompt_template = PromptTemplate(
    template="""{system_prompt}

Твой id: {discord_id}
Твой name: {discord_name}

История чата: {history}
""",
    input_variables=["system_prompt", "discord_id", "discord_name", "history"],
)


async def gen_msg_node(state: IdentityState) -> IdentityState:
    """
    Узел генерации ответа в чате.
    """
    try:
        history = f"[{',\n'.join(msg.model_dump_json(indent=4, ensure_ascii=True) for msg in state.messages)}]"
        chain = gen_msg_prompt_template | state.main_llm
        response = await chain.ainvoke(
            {
                "system_prompt": state.system_message.content + state.system_prompt,
                "discord_id": state.discord_id,
                "discord_name": state.discord_name,
                "history": history,
            }
        )
        return {"response_msg": response}
    except Exception:
        logger.exception("ОШИБКА в Узел генерации ответа в чате.")
        return {"response_msg": None}


async def validate_msg_node(state: IdentityState) -> IdentityState:
    validation_result = {"validation_response": ValidationResponse(validation_status="approve")}
    return validation_result


async def validate_msg_classificator(state: IdentityState) -> Literal["reject", "approve"]:
    return state.validation_response.validation_status


graph = StateGraph(IdentityState)

graph.add_node("gen_msg_node", gen_msg_node)
graph.add_node("validate_msg_node", validate_msg_node)

graph.add_edge(START, "gen_msg_node")
graph.add_edge("gen_msg_node", "validate_msg_node")
graph.add_conditional_edges(
    "validate_msg_node",
    validate_msg_classificator,
    {
        "reject": "gen_msg_node",
        "approve": END,
    },
)

app = graph.compile()
