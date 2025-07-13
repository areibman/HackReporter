from crewai.tools import BaseTool
from typing import Type, Any, List, Dict
from pydantic import BaseModel, Field
import tweepy
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
        "Search Twitter/X to find user profiles based on name and context. "
        "Useful for finding hackathon attendees' social media handles."
    )
    args_schema: Type[BaseModel] = TwitterSearchToolInput

    def _run(
        self,
        name: str,
        additional_context: str = ""
    ) -> str:
        """
        Search for a person's Twitter/X profile.

        Args:
            name: Person's name to search for
            additional_context: Additional search context

        Returns:
            Search results with potential profile matches
        """
        try:
            # Get Twitter API credentials
            bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
            if not bearer_token:
                return "Error: TWITTER_BEARER_TOKEN environment variable not set"

            # Initialize Tweepy client
            client = tweepy.Client(bearer_token=bearer_token)

            # Construct search query
            search_query = f"{name}"
            if additional_context:
                search_query += f" {additional_context}"

            # Search for users
            users = client.search_users(
                query=search_query,
                max_results=10,
                user_fields=['id', 'name', 'username', 'description', 'verified', 'public_metrics']
            )

            if not users.data:
                return f"No Twitter/X profiles found for '{name}'"

            # Format results
            results = f"Twitter/X Profile Search Results for '{name}':\n\n"

            for i, user in enumerate(users.data, 1):
                results += f"{i}. @{user.username}\n"
                results += f"   Name: {user.name}\n"
                results += f"   Bio: {user.description[:100]}...\n" if user.description else ""
                results += f"   Followers: {user.public_metrics['followers_count']}\n"
                results += f"   Verified: {'Yes' if user.verified else 'No'}\n"
                results += f"   Profile: https://twitter.com/{user.username}\n\n"

            return results

        except tweepy.TooManyRequests:
            return "Error: Twitter API rate limit exceeded. Please try again later."
        except Exception as e:
            return f"Error searching Twitter/X: {str(e)}"
