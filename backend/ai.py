import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )

    response.raise_for_status()

    data = response.json()
    return data["response"]