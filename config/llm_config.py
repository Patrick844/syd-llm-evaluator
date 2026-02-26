import dotenv
import os
from openai import OpenAI

# Load .env variables at import time.
dotenv.load_dotenv()

# Base URL for custom OpenAI-compatible endpoint.
# NOTE: Empty env key means this is usually None.
url= os.getenv("")

# Standard OpenAI API key from environment.
api_key = os.getenv("OPENAI_API_KEY")


class LLM_OPENAI:
    def __init__(self,config):
        # Store runtime model/prompt/response settings.
        self.config = config

        # Initialize OpenAI client once per service instance.
        self.client = OpenAI(
        base_url=url,
        api_key=api_key,
        )

    def invoke(self,user_message, response_template=None):
        """
        Send prompt to model and return either:
        - parsed structured output (when response_type == structured_output), or
        - raw text + response object (fallback path).
        """
        try:
            response_type = self.config["response_type"]
            system_prompt = self.config["system_prompt"]
            model_name = self.config["model_name"]
        except KeyError as e:
            raise ValueError(f"Missing required LLM config key: {e}") from e

        print("Response Type: ",response_type)

        if response_type=="structured_output":
            # Convert prompts into role-based messages for Responses API.
            user_message = {"role": "user", "content": user_message}
            system_prompt = {"role": "system", "content": system_prompt}
            try:
                completion = self.client.responses.parse(
                model=model_name,
                max_output_tokens=4096,
                input = [
                    system_prompt,
                    user_message
                ],
                text_format=response_template
                )
            except Exception as e:
                raise RuntimeError(f"Structured LLM request failed: {e}") from e
            print(completion)

            # Parsed object follows the provided pydantic schema.
            response = completion.output_parsed

            print("Generate Response\n")
            print("\nUser Message: ",user_message)
            print("AI Assistant: ", response)
            return response

        else:
            # Fallback plain chat-completions path.
            try:
                response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0
            )
            except Exception as e:
                raise RuntimeError(f"Chat completion request failed: {e}") from e
            print("Generate Response\n")
            print("\nUser Message: ",user_message)
            print("AI Assistant: ", response)
            return response.choices[0].message.content.strip(), response