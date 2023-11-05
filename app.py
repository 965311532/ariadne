import requests
from decouple import config
from flask import Flask, request

RELEVANTAI_PROJECT_ID = str(config("RELEVANTAI_PROJECT_ID"))
RELEVANTAI_API_URL = str(config("RELEVANTAI_API_URL"))

app = Flask(__name__)


@app.route("/")
def home():
    """Home page."""
    return "everything is working"


@app.route("/relay-email-webhook/", methods=["POST"])
def relay_email_webhook_from_zapier():
    """Relay email webhook from Zapier to RelevanAI."""
    print("Relaying email webhook from Zapier to RelevanAI")
    print(request.get_json())
    # Get the data from the request
    data = {"params": request.get_json(), "project": RELEVANTAI_PROJECT_ID}
    # Send the data to RelevantAI and wait for the response
    response = requests.post(RELEVANTAI_API_URL, json=data)
    # Return the response from RelevanAI
    return response.json()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config("PORT", default=5000))
