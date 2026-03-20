import requests

url = "https://www.munalbaraili.com/llm"
payload = {
    "model": "qwen2.5:7b",
    "prompt": "What is Spiderman."
}
headers = {"x-api-key": "mysecretkey"}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.text)