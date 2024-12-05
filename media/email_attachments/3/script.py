import requests

apisignin_url = "http://localhost:8010/api/signin/"
apipatch_url = "http://localhost:8000/api/patchTicket/"

data = {
  "email" : "alibayar111@gmail.com",
  "password": "password",
  "role": "member"
}

# sign in
responce = requests.post(apisignin_url, data)

# get access token
access_token =  responce.text#[17:]

print("access_token",access_token)


#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFsaWJheWFyQGdtYWlsLmNvbSIsInJvbGUiOiJtZW1iZXIifQ.9z9jAQJm-y8lLBdOaJscYUtuuKvy-xvvw-OcKYM1Uz4