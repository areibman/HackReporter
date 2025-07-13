from crewai.tools import BaseTool
from typing import Type, Any, List, Dict
from pydantic import BaseModel, Field
from openai import OpenAI
import os


class TwitterSearchToolInput(BaseModel):
    """Input schema for TwitterSearchTool."""
    name: str = Field(description="Name of the person to search for")
    additional_context: str = Field(
        default="",
        description="Additional context like company, hackathon name, etc."
    )


class TwitterSearchTool(BaseTool):
    name: str = "twitter_profile_finder"
    description: str = (
        "Search for Twitter/X profiles using Exa Deep Search API. "
        "Finds user profiles based on name and context. "
        "Useful for finding hackathon attendees' social media handles."
    )
    args_schema: Type[BaseModel] = TwitterSearchToolInput

    def _run(
        self,
        name: str,
        additional_context: str = ""
    ) -> str:
        """
        Search for a person's Twitter/X profile using Exa Deep Search.

        Args:
            name: Person's name to search for
            additional_context: Additional search context

        Returns:
            Search results with potential profile matches
        """
        try:
            # Get Exa API key
            api_key = os.getenv("EXA_API_KEY", "740fa2f0-48aa-4d69-b171-4831dc1d92ff")
            if not api_key:
                return "Error: EXA_API_KEY environment variable not set"

            # Initialize OpenAI client with Exa's base URL
            client = OpenAI(
                base_url="https://api.exa.ai",
                api_key=api_key,
            )

            # Construct the search prompt
            prompt = f"Find the Twitter/X.com handle for {name}."
            if additional_context:
                prompt += f" Additional context: {additional_context}."
            prompt += " If the name is common, assume they work in tech. Provide their Twitter/X handle (@username) and a brief description of who they are."

            # Use Exa's research model to find Twitter handles
            completion = client.chat.completions.create(
                model="exa-research-pro",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=False  # Get complete response at once
            )

            # Extract the response
            response = completion.choices[0].message.content

            # Format the results
            results = f"Twitter/X Profile Search Results for '{name}':\n\n"
            if response:
                results += response
            else:
                results += "No response received from Exa API."

            return results

        except Exception as e:
            return f"Error searching for Twitter/X profile: {str(e)}"
