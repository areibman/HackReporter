from crewai.tools import BaseTool
from typing import Type, Any, List, Dict, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with formatting
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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
        logger.info("Starting Twitter profile search")
        logger.debug(f"Names: {names}")
        logger.debug(f"Companies/Tech: {companies_or_tech}")
        logger.debug(f"Additional context: {additional_context}")

        try:
            # Get Exa API key
            api_key = os.getenv("EXA_API_KEY", "740fa2f0-48aa-4d69-b171-4831dc1d92ff")
            if not api_key:
                logger.error("EXA_API_KEY environment variable not set")
                return "Error: EXA_API_KEY environment variable not set"

            logger.debug("Initializing OpenAI client with Exa API")
            # Initialize OpenAI client with Exa's base URL
            client = OpenAI(
                base_url="https://api.exa.ai",
                api_key=api_key,
            )

            # Build a comprehensive prompt for all entities
            prompt_parts = []

            # Add context if available
            if additional_context:
                prompt_parts.append(f"Context: {additional_context}")

            prompt_parts.append("Find Twitter/X handles for the following:")

            # Add people names
            if names:
                prompt_parts.append("\nPeople (assume they work in tech):")
                for name in names:
                    prompt_parts.append(f"- {name}")

            # Add companies/technologies
            if companies_or_tech:
                prompt_parts.append("\nCompanies/Technologies/Tools:")
                for entity in companies_or_tech:
                    prompt_parts.append(f"- {entity}")

            # If no specific names or companies, use contextual search
            if not names and not companies_or_tech:
                if additional_context:
                    prompt_parts = [
                        f"Based on this context: {additional_context}",
                        "Identify any relevant Twitter/X handles for people, companies, or technologies mentioned.",
                        "Focus on tech-related accounts."
                    ]
                else:
                    logger.warning("No names, companies, or context provided")
                    return "No names, companies, or context provided for search."

            # Complete the prompt
            prompt_parts.extend([
                "\nFor each entity, provide:",
                "1. Their Twitter/X handle (@username)",
                "2. A brief description to verify it's the correct account",
                "3. If you cannot find a handle, say 'Handle not found' and explain why",
                "\nEnsure all handles are for Twitter/X accounts, not other social media."
            ])

            prompt = "\n".join(prompt_parts)
            logger.debug(f"Combined search prompt: {prompt}")

            # Make a single API call
            logger.info("Making API call to Exa search")
            completion = client.chat.completions.create(
                model="exa-research",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )

            response = completion.choices[0].message.content
            logger.debug(f"API response: {response}")

            if response:
                results = "Twitter/X Profile Search Results:\n\n"
                results += response
                logger.info("Twitter profile search completed successfully")
                return results
            else:
                logger.warning("No response received from API")
                return "No response received from search API."

        except Exception as e:
            logger.error(f"Error during Twitter profile search: {str(e)}", exc_info=True)
            return f"Error searching for Twitter/X profiles: {str(e)}"
