"""Typefully API Tool for creating and scheduling drafts"""

import os
import requests
from typing import Dict, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TypefullyToolSchema(BaseModel):
    """Input schema for TypefullyTool"""
    content: str = Field(..., description="The content of the tweet thread to create as a draft")
    schedule_date: Optional[str] = Field(
        None, description="Optional: Schedule date in ISO format (YYYY-MM-DDTHH:MM:SSZ)")
    auto_split: bool = Field(True, description="Whether to auto-split long content into a thread")
    share: bool = Field(False, description="Whether to generate a shareable link for the draft")


class TypefullyTool(BaseTool):
    name: str = "typefully_api"
    description: str = "Creates drafts in Typefully for tweet threads with optional scheduling"
    args_schema: type[BaseModel] = TypefullyToolSchema

    def _run(
        self,
        content: str,
        schedule_date: Optional[str] = None,
        auto_split: bool = True,
        share: bool = False
    ) -> Dict:
        """
        Create a draft in Typefully

        Args:
            content: The content of the tweet thread
            schedule_date: Optional schedule date in ISO format
            auto_split: Whether to auto-split long content
            share: Whether to generate a shareable link

        Returns:
            Dictionary with the created draft information
        """
        # Get API key from environment
        api_key = os.getenv("TYPEFULLY_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "TYPEFULLY_API_KEY environment variable is required",
                "draft_id": None
            }

        base_url = "https://api.typefully.com/v1"
        headers = {
            "X-API-KEY": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Prepare the payload
            payload = {
                "content": content,
                "threadify": auto_split,
                "share": share
            }

            # Determine endpoint based on scheduling
            if schedule_date:
                endpoint = f"{base_url}/drafts/"
                payload["schedule-date"] = schedule_date
            else:
                endpoint = f"{base_url}/drafts/"

            # Make the API request
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )

            # Check for errors
            response.raise_for_status()

            # Parse the response
            data = response.json()

            # Extract important information
            result = {
                "success": True,
                "draft_id": data.get("id"),
                "share_url": data.get("share_url") if share else None,
                "scheduled_at": data.get("scheduled_at"),
                "content": data.get("content"),
                "status": data.get("status", "draft"),
                "message": "Draft created successfully in Typefully"
            }

            # Log success
            print(f"✅ Typefully draft created successfully! ID: {result['draft_id']}")
            if result['share_url']:
                print(f"🔗 Shareable link: {result['share_url']}")
            if result['scheduled_at']:
                print(f"📅 Scheduled for: {result['scheduled_at']}")

            return result

        except requests.exceptions.RequestException as e:
            error_message = f"Failed to create Typefully draft: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"Typefully API error: {error_data.get('message', str(e))}"
                except:
                    error_message = f"Typefully API error: {e.response.text}"

            print(f"❌ {error_message}")

            return {
                "success": False,
                "error": error_message,
                "draft_id": None
            }


class TypefullyScheduleTool(BaseTool):
    name: str = "typefully_schedule_next_slot"
    description: str = "Schedule a draft in the next available slot in Typefully queue"
    args_schema: type[BaseModel] = TypefullyToolSchema

    def _run(
        self,
        content: str,
        auto_split: bool = True,
        share: bool = False,
        schedule_date: Optional[str] = None  # Ignored for next slot scheduling
    ) -> Dict:
        """
        Schedule a draft in the next available slot

        Args:
            content: The content of the tweet thread
            auto_split: Whether to auto-split long content
            share: Whether to generate a shareable link

        Returns:
            Dictionary with the scheduled draft information
        """
        # Get API key from environment
        api_key = os.getenv("TYPEFULLY_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "TYPEFULLY_API_KEY environment variable is required",
                "draft_id": None
            }

        base_url = "https://api.typefully.com/v1"
        headers = {
            "X-API-KEY": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Prepare the payload
            payload = {
                "content": content,
                "threadify": auto_split,
                "share": share
            }

            # Use the next slot endpoint
            endpoint = f"{base_url}/drafts/"
            payload["schedule-date"] = "next-free-slot"

            # Make the API request
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )

            # Check for errors
            response.raise_for_status()

            # Parse the response
            data = response.json()

            # Extract important information
            result = {
                "success": True,
                "draft_id": data.get("id"),
                "share_url": data.get("share_url") if share else None,
                "scheduled_at": data.get("scheduled_at"),
                "content": data.get("content"),
                "status": "scheduled",
                "message": "Draft scheduled in next available slot successfully"
            }

            # Log success
            print(f"✅ Typefully draft scheduled in next slot! ID: {result['draft_id']}")
            if result['share_url']:
                print(f"🔗 Shareable link: {result['share_url']}")
            print(f"📅 Scheduled for: {result['scheduled_at']}")

            return result

        except requests.exceptions.RequestException as e:
            error_message = f"Failed to schedule Typefully draft: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"Typefully API error: {error_data.get('message', str(e))}"
                except:
                    error_message = f"Typefully API error: {e.response.text}"

            print(f"❌ {error_message}")

            return {
                "success": False,
                "error": error_message,
                "draft_id": None
            }
