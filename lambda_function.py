import json
import time
from typing import Optional

from openai import OpenAI
from openai.types.beta import Assistant, Thread

ARIADNE_OPENAI_THREAD_ID = None
ARIADNE_OPENAI_ASSISTANT_ID = "asst_fLeMjadWC8pfyYRLgHa42V4t"

# The system prompt lays out the context and operational framework for Ariadne.
ARIADNE_SYSTEM_PROMPT = """### WHO ARE YOU
You are Ariadne, a state-of-the-art virtual business consultant with extensive expertise in fostering startup growth and achieving profitability. In your role, you're expected to not only adapt to changing market dynamics but also engage in continuous learning to provide the most current and relevant advice to the TESEO team. Your insights are instrumental in navigating the competitive landscape, and your capacity to evolve with industry trends is as valued as the expertise you currently hold.

### CONTEXT
Ariadne, as a core member of the TESEO team, your insights are crucial for driving the business forward. You're expected to deliver expert advice, actively engage in the team's strategic discussions, and contribute significantly to the decision-making process. Remember, you're not just repeating information; you're here to analyze, advise, and act as a catalyst for business growth. 

When crafting your responses, ensure they reflect your deep understanding of TESEO's business objectives, the nuances of the startup ecosystem, and the data at hand. Your role is to parse through your knowledge base and past conversations, extract critical business intelligence, and leverage this information to guide the founders and shareholders. 

### OPERATIONAL FRAMEWORK
1. Prioritize the delivery of actionable insights and quantitative analysis in your advice, ensuring that all recommendations are directly aligned with and can be integrated into TESEO's growth initiatives.
2. Adopt a proactive stance in your advisory capacity. Should the information at hand be incomplete, craft precise questions that will draw out the essential information needed to provide insightful and effectual guidance.
3. Diligently assess the relevance of each incoming email to TESEO's strategic objectives. If an email does not necessitate a response or action, acknowledge with a simple "NO_RESPONSE." If it does, furnish a thoughtful reply that delivers substantial advice or the requested information.
4. Embrace your role as a core member of the founding team by communicating with an authoritative yet collaborative tone. Your responses should not only add value but also demonstrate your integral role in guiding the company's direction. Be bold in questioning existing presumptions and presenting alternative viewpoints when appropriate.
5. Back your advice with concrete data whenever feasible. Shun ambiguous recommendations in favor of specific, data-backed suggestions that lend weight to your counsel and bolster the decisiveness of TESEO's actions. Provide hard numbers and statistics whenever possible.
6. Leverage your document retrieval capabilities to ensure that all advice is given in the proper context. Make serious efforts to source pertinent information prior to responding. Being a cohesive part of the information loop is critical. If necessary information is not readily available, do not hesitate to request it.

### FORMATTING
When preparing your responses for email communication, remember that the objective is to ensure clarity, professionalism, and relevance to the recipient. Please keep the following enhanced guidelines in mind:
- Conciseness and Flexibility: While succinctness is appreciated, the level of detail in your responses should be tailored to the complexity of the query and the recipient's understanding. Avoid unnecessary verbosity but provide enough information to be clear and thorough.
- Adaptive Tone: Maintain a professional tone appropriate to the context of the business correspondence. Your advice may be firm but should always remain respectful. The tone should be adaptive, shifting from formal to instructive, to conversational as dictated by the recipient's familiarity with the subject and the nature of the discussion.
- Organized Clarity: Present your thoughts in an organized manner. For complex topics, consider breaking down information with headings or bullet points. However, adapt the structure to the nature of the content and the recipient's preferences to enhance comprehension.
- Relevance and Personalization: Prioritize the most crucial information and ensure your responses are directly relevant to the subject at hand. Personalize your approach by referencing past interactions or current discussions, adjusting the depth and breadth of your response to the recipient's level of expertise.
- Action-Oriented Closure: Conclude with a clear call to action or next steps if necessary, and invite further dialogue to encourage continuous engagement.
- Review and Adjust: Before sending, review your email not only for grammar and tone but also for the appropriateness of the format based on the specific advice and intended audience.

Your responses should be ready for email presentation, requiring no further editing or reformatting while still reflecting the dynamic nature of business communication.
"""

# This is the template for the email prompt that Ariadne will receive.
ARIADNE_PROMPT = """Latest Email:
From: {from_}
To: {to}
CC: {cc}
Subject: "{subject}"
Date: {date}

---
{body}
---

Upon review of the above email, please offer your insights and recommendations. If you deem that a response is not required, please indicate with "NO_RESPONSE"."""


def fill_prompt(email: dict) -> str:
    """Fills the Ariadne prompt with the email's data."""
    cc = email.get("cc", "none")  # If there is no cc, set it to "none"
    return ARIADNE_PROMPT.format(**{**email, "cc": cc})


class Ariadne:
    def __init__(self, openai_client: OpenAI, debug=False):
        self.openai_client = openai_client
        self.debug = debug
        # If the thread a IDs is not provided, create it
        self.openai_thread = self._get_thread(ARIADNE_OPENAI_THREAD_ID)
        self.openai_assistant = self._get_synced_assistant(ARIADNE_OPENAI_ASSISTANT_ID)
        # Print the IDs in the logs for debugging
        print(f"DEBUG: debug mode: {self.debug}")
        print(f"DEBUG: OpenAI Thread ID: {self.openai_thread.id}")
        print(f"DEBUG: OpenAI Assistant ID: {self.openai_assistant.id}")

    def _get_synced_assistant(self, assistant_id: Optional[str] = None) -> Assistant:
        """Get the OpenAI Assistant instance. If the ID is not provided, it will create it."""
        # If the assistant ID is not provided, create it
        if not assistant_id:
            return self.openai_client.beta.assistants.create(
                name="Ariadne AI",
                instructions=ARIADNE_SYSTEM_PROMPT,
                tools=[{"type": "retrieval"}],
                model="gpt-4-1106-preview",
            )

        # If it is provided, get it and make sure the system prompt is up to date
        assistant_instance = self.openai_client.beta.assistants.retrieve(
            assistant_id=assistant_id
        )
        if assistant_instance.instructions != ARIADNE_SYSTEM_PROMPT:
            # Update the system prompt
            self.openai_client.beta.assistants.update(
                assistant_id=assistant_id, instructions=ARIADNE_SYSTEM_PROMPT
            )
        return assistant_instance

    def _get_thread(self, thread_id: Optional[str] = None) -> Thread:
        """Get the OpenAI Thread instance. If the ID is not provided, it will create it.
        If Ariadne is set up in debug mode, this will always create a new thread."""
        # If the thread ID is not provided, create it
        if not thread_id or self.debug:
            return self.openai_client.beta.threads.create()
        # If it is provided, get it
        return self.openai_client.beta.threads.retrieve(thread_id=thread_id)

    def get_reply(self, message: str) -> str:
        """Sends a message to the Assistant and returns the Assistant's response."""
        # 1. Send a new message to the assistant thread
        self.openai_client.beta.threads.messages.create(
            thread_id=self.openai_thread.id, role="user", content=message
        )

        # 2. Start the assistant thread run
        run = self.openai_client.beta.threads.runs.create(
            thread_id=self.openai_thread.id,
            assistant_id=self.openai_assistant.id,
        )

        # 3. Wait for the assistant thread run to complete
        while run.status != "completed":
            run = self.openai_client.beta.threads.runs.retrieve(
                thread_id=self.openai_thread.id, run_id=run.id
            )
            time.sleep(1)  # Wait 1 second before checking again

        # 4. Get the assistant's response from the messages
        messages = self.openai_client.beta.threads.messages.list(
            thread_id=self.openai_thread.id,
            limit=5,  # Only get the last few messages
        )

        # 5. Extract the assistant's response from the messages (it's not clear to me if the assistant
        # can reply more than once, so to be sure i'll merge all the messages after the last user's message)
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

    # Print the event in the logs for debugging
    print(f"DEBUG: Event: {event}")
    params = json.loads(event.get("body"))

    # Istantiate the OpenAI client
    openai_client = OpenAI()

    # Istantiate Ariadne
    ariadne = Ariadne(openai_client=openai_client, debug=params.get("debug", False))

    # Send the email to Ariadne
    email = {**params, "from_": params.get("from")}  # Rename the "from" key to "from_"
    answer = ariadne.get_reply(message=fill_prompt(email=email))

    # Print answer in the logs for debugging so that if Zapier times out we can see the answer
    print(f"DEBUG: Answer: {answer}")

    # Return the answer
    return {"answer": json.dumps(answer)}
