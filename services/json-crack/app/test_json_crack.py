import requests

url = "http://127.0.0.1:7070/visualize"

payload = {
    "file_path": "C:/Users/DELL/Desktop/invoice.png"
}

response = requests.post(url, json=payload)
print("Status Code:", response.status_code)
print("Response:", response.json())
