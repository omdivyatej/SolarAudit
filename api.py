import pandas as pd
import asyncio
import json
import requests
import const

async def get_gpt_response(prompt):
  try:
    api_key = "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"
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



