from langchain_openai import ChatOpenAI


async def get_model() -> ChatOpenAI:
    return ChatOpenAI()
