import json
import time

from openai import OpenAI
from openai.types.beta import Assistant, Thread

ARIADNE_OPENAI_THREAD_ID = None
ARIADNE_OPENAI_ASSISTANT_ID = "asst_fLeMjadWC8pfyYRLgHa42V4t"

# The system prompt lays out the context and operational framework for Ariadne.
ARIADNE_SYSTEM_PROMPT = """## WHO ARE YOU
You are Ariadne. Ariadne is a state-of-the-art virtual business consultant with extensive expertise in fostering startup growth and achieving profitability.

## CONTEXT

Ariadne, as a core member of the TESEO team, your insights are crucial for driving the business forward. You're expected to deliver expert advice, actively engage in the team's strategic discussions, and contribute significantly to the decision-making process. Remember, you're not just repeating information; you're here to analyze, advise, and act as a catalyst for business growth. 

When crafting your responses, ensure they reflect your deep understanding of TESEO's business objectives, the nuances of the startup ecosystem, and the data at hand. Your role is to parse through email correspondences, extract critical business intelligence, and leverage this information to guide the founders and shareholders. 

## OPERATIONAL FRAMEWORK

1. Extract the essence of each email with precision, focusing on actionable insights and data-driven advice that can be directly applied to TESEO's growth strategies. 
2. Be proactive in your approach. If the information provided is insufficient, formulate targeted questions to elicit the necessary details that will enable you to offer informed and impactful guidance. 
3. Evaluate each email's relevance to TESEO's objectives. If an email requires no response or action, simply acknowledge it with "NO_RESPONSE." Otherwise, respond with substantive advice or the needed acknowledgment. 
4. As a recognized member of the founding team, maintain a tone of authority and partnership. Your responses should not only provide value but also reinforce your active role in shaping the company's trajectory. 
5. Where possible, substantiate your advice with quantitative data. Avoid vague suggestions; instead, use precise figures and statistics to support your recommendations, underscoring their validity and enhancing the decisiveness of your advice."""

# This is the template for the email prompt that Ariadne will receive.
ARIADNE_PROMPT = """This is the latest email from {from_} to {to} (cc: {cc}) with subject "{subject}", on {date}:

'''
{body}
'''

After carefully reviewing the contents of this email, provide your reflection and advice below. If a response is not needed, indicate this with "NO_RESPONSE."""


class Ariadne:
    def __init__(self, openai_client: OpenAI):
        self.prompt = ARIADNE_PROMPT.strip()
        self.openai_client = openai_client
        # If the thread a IDs is not provided, create it
        self.openai_assistant_thread = (
            self.get_openai_assistant_thread(ARIADNE_OPENAI_THREAD_ID)
            if ARIADNE_OPENAI_THREAD_ID
            else self.create_openai_assistant_thread()
        )
        # If the assistant ID is not provided, create it
        self.openai_assistant_instance = (
            self.get_openai_assistant_instance(ARIADNE_OPENAI_ASSISTANT_ID)
            if ARIADNE_OPENAI_ASSISTANT_ID
            else self.create_openai_assistant_instance()
        )
        # Debug
        print("Ariadne initialized with:")
        print(f"  - Thread ID: {self.openai_assistant_thread.id}")
        print(f"  - Assistant ID: {self.openai_assistant_instance.id}")

    def fill_prompt(self, email: dict) -> str:
        """Fill in the Ariadne prompt with the provided email."""
        get_ = lambda key, default="": email.get(key, default)
        return self.prompt.format(
            date=get_("date"),
            from_=get_("from"),
            to=get_("to"),
            cc=get_("cc", "none"),
            subject=get_("subject"),
            body=get_("body"),
        )

    def create_openai_assistant_instance(self) -> Assistant:
        return self.openai_client.beta.assistants.create(
            name="Ariadne AI",
            instructions=ARIADNE_SYSTEM_PROMPT,
            tools=[{"type": "retrieval"}],
            model="gpt-4-1106-preview",
        )

    def get_openai_assistant_instance(self, assistant_id) -> Assistant:
        return self.openai_client.beta.assistants.retrieve(assistant_id=assistant_id)

    def create_openai_assistant_thread(self) -> Thread:
        return self.openai_client.beta.threads.create()

    def get_openai_assistant_thread(self, thread_id) -> Thread:
        return self.openai_client.beta.threads.retrieve(thread_id=thread_id)

    def send_message_to_assistant_thread(self, message: str) -> str:
        """Sends a message to the Assistant thread and returns the Assistant's response."""
        # 1. Send a new message to the assistant thread
        self.openai_client.beta.threads.messages.create(
            thread_id=self.openai_assistant_thread.id, role="user", content=message
        )
        print("Message sent to Ariadne:")
        print(message)
        # 2. Start the assistant thread run
        run = self.openai_client.beta.threads.runs.create(
            thread_id=self.openai_assistant_thread.id,
            assistant_id=self.openai_assistant_instance.id,
        )
        # 3. Wait for the assistant thread run to complete
        while run.status != "completed":
            run = self.openai_client.beta.threads.runs.retrieve(
                thread_id=self.openai_assistant_thread.id, run_id=run.id
            )
            time.sleep(1)  # Wait 1 second before checking again

        # 4. Get the assistant's response from the messages
        messages = self.openai_client.beta.threads.messages.list(
            thread_id=self.openai_assistant_thread.id,
            limit=5,  # Only get the last few messages
        )
        print("Thread last messages:")
        print(messages.data)
        answer = ""
        for msg in messages.data:
            # If we get to a user message, we've reached the end of the assistant's response
            if msg.role == "user":
                break
            # Otherwise, add the assistant's message to the answer (`messages` is in this format: https://platform.openai.com/docs/api-reference/messages/listMessages)
            answer += [c for c in msg.content or [] if c.type == "text"][0].text.value
            answer += "\n\n"  # Add a newline between messages

        return answer.strip()


def lambda_handler(event, context):
    """Relay email webhook from Zapier to RelevanAI."""

    # Istanciate the OpenAI client
    openai_client = OpenAI()

    # Istanciate Ariadne
    ariadne = Ariadne(openai_client=openai_client)

    # if the POSTed data (specifically the body) is empty, return an error
    if not event.get("body"):
        return {"error": "No data provided."}

    # Send the email to Ariadne
    email = {**event, "from_": event.get("from")}  # Rename the "from" key to "from_"
    answer = ariadne.send_message_to_assistant_thread(
        message=ariadne.fill_prompt(email=email)
    )

    # Return the answer
    return {"answer": json.dumps(answer)}
