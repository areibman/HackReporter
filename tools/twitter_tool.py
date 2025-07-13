from crewai.tools import BaseTool
from typing import Type, Any, List, Dict, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
import os


class TwitterSearchToolInput(BaseModel):
    """Input schema for TwitterSearchTool."""
    names: List[str] = Field(
        default=[],
        description="List of person names to search for (can be empty if names aren't available)"
    )
    companies_or_tech: List[str] = Field(
        default=[],
        description="List of companies, technologies, or tools mentioned (e.g., 'OpenAI', 'React', 'MongoDB')"
    )
    additional_context: str = Field(
        default="",
        description="Additional context like hackathon name, project description, etc."
    )


class TwitterSearchTool(BaseTool):
    name: str = "twitter_profile_finder"
    description: str = (
        "Search for Twitter/X profiles using Exa Deep Search API. "
        "Finds profiles for people, companies, and technologies. "
        "Handles multiple team members and missing names gracefully. "
        "Useful for finding hackathon attendees and related tech accounts."
    )
    args_schema: Type[BaseModel] = TwitterSearchToolInput

    def _run(
        self,
        names: List[str] = [],
        companies_or_tech: List[str] = [],
        additional_context: str = ""
    ) -> str:
        """
        Search for Twitter/X profiles using Exa Deep Search.

        Args:
            names: List of person names to search for
            companies_or_tech: List of companies or technologies to find handles for
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

            results = "Twitter/X Profile Search Results:\n\n"

            # Handle case when no names are available
            if not names and not companies_or_tech:
                if additional_context:
                    prompt = (
                        f"Based on this context: {additional_context}, "
                        "identify any relevant Twitter/X handles for people, companies, or technologies mentioned. Provide their @'s (handles) but ensure it is for their twitter/x account."
                        "Focus on tech-related accounts."
                    )

                    completion = client.chat.completions.create(
                        # model="exa-research-pro",
                        model="exa-research",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False
                    )

                    response = completion.choices[0].message.content
                    if response:
                        results += "**Contextual Search Results:**\n"
                        results += response + "\n\n"
                    else:
                        results += "No relevant Twitter/X handles found based on the provided context.\n\n"
                else:
                    results += "No names or context provided for search.\n\n"

            # Search for each person
            if names:
                results += "**Team Members:**\n"
                for name in names:
                    prompt = (
                        f"Find the Twitter/X.com handle for {name}. "
                        f"Assume they work in tech. "
                    )
                    if additional_context:
                        prompt += f"Additional context: {additional_context}. "
                    prompt += (
                        "Provide their Twitter/X handle (@username) and a brief description. "
                        "If you cannot find their handle, say 'Handle not found' and explain why."
                    )

                    completion = client.chat.completions.create(
                        model="exa-research-pro",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False
                    )

                    response = completion.choices[0].message.content
                    if response:
                        results += f"\n{name}:\n{response}\n"
                    else:
                        results += f"\n{name}: No response received from search.\n"

                results += "\n"

            # Search for companies and technologies
            if companies_or_tech:
                results += "**Companies/Technologies:**\n"
                for entity in companies_or_tech:
                    prompt = (
                        f"Find the official Twitter/X.com handle for {entity}. "
                        "This could be a company, technology, framework, or tool. "
                        "Provide the official handle (@username) and verify it's the correct official account."
                    )

                    completion = client.chat.completions.create(
                        model="exa-research-pro",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False
                    )

                    response = completion.choices[0].message.content
                    if response:
                        results += f"\n{entity}:\n{response}\n"
                    else:
                        results += f"\n{entity}: No response received from search.\n"

            return results

        except Exception as e:
            return f"Error searching for Twitter/X profiles: {str(e)}"
