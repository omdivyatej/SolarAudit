import pandas as pd
import asyncio
import json
import requests
import const
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now you can safely get the environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
async def get_gpt_response(prompt):
  try:
    api_key = openai_api_key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4-1106-preview",
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": const.SYSTEM_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": const.GPT_PROMPT
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 3000
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    openai_response = response.json()
    print(openai_response)
    json_string = openai_response["choices"][0]["message"]["content"]
    print(json_string)
    json_string = json_string.replace("```json", "").strip()
    json_string = json_string.replace("```", "").strip()
    json_object = json.loads(json_string)
    return json_object
  except Exception as e:
      print(e)



