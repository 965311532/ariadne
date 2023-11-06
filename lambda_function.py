import json
import os

import urllib3

RELEVANTAI_PROJECT_ID = os.environ.get("RELEVANTAI_PROJECT_ID")
RELEVANTAI_API_URL = os.environ.get("RELEVANTAI_API_URL")


def lambda_handler(event, context):
    """Relay email webhook from Zapier to RelevanAI."""

    # If the environment variables are not set, raise an error
    if not RELEVANTAI_PROJECT_ID or not RELEVANTAI_API_URL:
        raise ValueError(
            "RELEVANTAI_PROJECT_ID and RELEVANTAI_API_URL environment variables must be set"
        )

    # Initialize a PoolManager instance
    http = urllib3.PoolManager()

    # Attempt to load the event body as JSON
    try:
        params = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        # In case the body is not valid JSON, set params to an empty object
        params = {}

    # Construct the data object with params as a JSON object
    data = {"params": params, "project": RELEVANTAI_PROJECT_ID}

    # Convert the data dictionary to JSON
    encoded_data = json.dumps(data).encode("utf-8")

    # Set headers for JSON content type
    headers = {"Content-Type": "application/json"}

    # Send the data to RelevantAI and wait for the response
    response = http.request(
        "POST", RELEVANTAI_API_URL, body=encoded_data, headers=headers
    )

    # Return the decoded response
    return json.loads(response.data.decode("utf-8"))
