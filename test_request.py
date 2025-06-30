import requests

headers = {
    "Authorization": "zjUOg74l.GzOLwkwKMRqWbUIcFRny98V1cXZC69Pj",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "PostmanRuntime/7.35.0"
}

params = {
    "student_id_number": "SSC20257279",
    "term": "2025-1"
}

url = "http://31.187.76.42/api/student/payments/"

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.text)
