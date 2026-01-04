#!/usr/bin/env python3
import requests
import json

url = "http://localhost:8082/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer hilt_sk_test123"
}

data = {
    "model": "gpt-4",
    "messages": [
        {"role": "user", "content": "What is the weather in San Francisco?"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
}

print("Sending request to HILT...")
response = requests.post(url, headers=headers, json=data, timeout=60)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
