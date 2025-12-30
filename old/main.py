  import os
import asyncio
import discord
from dotenv import load_dotenv
import yaml
import sys
print("Python path:", sys.path)
print("Looking for agents.agent in:", sys.modules.get("agents.agent"))
from agents.agent import AIAgent
from agents.personality import get_personality

load_dotenv()

with open("config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Intents не нужны для self-ботов
intents = None

# Запуск двух агентов
async def run_agent(token, partner_id, personality_name):
    client = discord.Client(intents=intents)
    agent = AIAgent(client, partner_id, config["servers"], get_personality(personality_name))

    @client.event
    async def on_ready():
        print(f"{client.user} готов к работе как {personality_name}!")

    @client.event
    async def on_message(message):
        await agent.on_message(message)

    await client.start(token)

async def main():
    ai1_token = os.getenv("DISCORD_TOKEN_AI1")
    ai2_token = os.getenv("DISCORD_TOKEN_AI2")
    
    print(f"AI1 Token (first 10): {ai1_token[:10] if ai1_token else 'None'}")
    print(f"AI2 Token (first 10): {ai2_token[:10] if ai2_token else 'None'}")

    ai1_task = run_agent(
        ai1_token,
        config["agents"]["ai2_user_id"],
        "technical"
    )
    ai2_task = run_agent(
        ai2_token,
        config["agents"]["ai1_user_id"],
        "social"
    )
    await asyncio.gather(ai1_task, ai2_task)

if __name__ == "__main__":
    asyncio.run(main())
