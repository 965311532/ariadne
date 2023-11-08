import json
import os
import sys

import urllib3
from openai import OpenAI

# Add the current directory to the path to enable absolute imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from ariadne import Ariadne, AriadnePrompt
from config import ARIADNE_EMAIL_ADDRESS, ZAPIER_WEBHOOK_URL


def lambda_handler(event, context):
    """Relay email webhook from Zapier to RelevanAI."""

    # Print the event in the logs for debugging
    print(f"DEBUG: Event: {event}")
    params = json.loads(event)  # Parse the event

    # Istantiate the OpenAI client
    openai_client = OpenAI()

    # Istantiate Ariadne
    ariadne = Ariadne(openai_client=openai_client, debug=params.get("debug", False))

    # Send the email to Ariadne
    email = {**params, "from_": params.get("from")}  # Rename the "from" key to "from_"
    answer = ariadne.get_reply(message=AriadnePrompt(email=email).build())

    # Print answer in the logs for debugging
    print(f"DEBUG: Answer: {answer}")

    # Remove empty and Ariadne's email address from the cc
    cc = params.get("cc", "") + "," + params.get("to")
    cc = ",".join([c for c in cc.split(",") if c != "" and c != ARIADNE_EMAIL_ADDRESS])

    # Call the zapier webhook to send the email
    http = urllib3.PoolManager()
    http.request(
        method="POST",
        url=ZAPIER_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        body=json.dumps(
            {
                "thread_id": params.get("thread_id"),
                "from": ARIADNE_EMAIL_ADDRESS,
                "to": params.get("from"),
                "cc": cc,
                "subject": f"Re: {params.get('subject')}",
                "body": answer,
            }
        ),
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "success"}),
    }
