# Ariadne Virtual Business Consultant

This repository contains the code for the Ariadne Virtual Business Consultant, an AI agent built to automate email responses and provide custom business advice.

## Overview

Ariadne is designed to assist startups by managing email communications and offering targeted business insights. This system uses AI models to parse emails, understand context, and deliver real-time, actionable advice based on a deep knowledge base tailored the company's specifics.

## Functionality

- Email Parsing: Ariadne processes incoming emails to understand the content and context.
- Advice Generation: Utilizes a predefined knowledge base to offer relevant business advice.
- AWS Lambda Integration: The core functionality is hosted on AWS Lambda for seamless scaling and management.
- Zapier Automation: Connects with Zapier to automate the email workflow process.

## Getting Started

The repository includes the code for the AWS Lambda function that you can deploy directly in your AWS environment. (I'll make a GH Action for continuous deployment soon.)

## Setting up the Lambda Function

- Deploy the Code: Upload the provided code to your AWS Lambda function.
- Zapier Integration: Configure your Zapier workflows to interact with the Lambda function, sending email data and receiving responses.

## Screenshot

### Zapier configuration

![Zapier configuration](assets/zapier-flow.png)

### RelevantAI LLM prompt

![RelevantAI LLM prompt](assets/relevantai-llm-config.png)

### Example response with annotations

![Example response](assets/example-response.png)
