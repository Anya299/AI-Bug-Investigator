from openai import AsyncOpenAI
import asyncio
from config import get_settings

settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url
)

async def test():
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {
                "role": "user",
                "content": "Say hello"
            }
        ]
    )

    print(response.choices[0].message.content)

asyncio.run(test())