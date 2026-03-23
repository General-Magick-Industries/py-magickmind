"""
Example: Setup Resources for SDK Examples

This script creates the necessary resources (EndUser, Project, Mindspace)
and updates your .env file with the IDs.

Demonstrates:
- Proper error handling with ProblemDetailsException
- Validation error handling with field-level details
- Resource creation with the simplified response models
"""

import asyncio
import os
import logging
from typing import Dict
from dotenv import load_dotenv, set_key

from magick_mind import MagickMind
from magick_mind.exceptions import (
    ProblemDetailsException,
    ValidationError,
    RateLimitError,
)

# Load existing .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("setup_resources")


def update_env_file(updates: Dict[str, str]):
    """Update or append keys to .env file."""
    env_path = ".env"
    if not os.path.exists(env_path):
        # Create if doesn't exist
        with open(env_path, "w") as f:
            f.write("")

    logger.info("\nUpdating .env file:")
    for key, value in updates.items():
        if value:
            # set_key updates the file in place
            set_key(env_path, key, value)
            logger.info(f"  - Set {key}={value}")


async def main():
    logger.info("=" * 60)
    logger.info("SDK RESOURCE SETUP")
    logger.info("=" * 60)

    # 1. Validate Credentials
    email = os.getenv("MAGICKMIND_EMAIL")
    password = os.getenv("MAGICKMIND_PASSWORD")
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://dev-api.magickmind.ai")
    ws_endpoint = os.getenv("MAGICKMIND_WS_ENDPOINT")

    if not email or not password:
        logger.error("ERROR: Missing credentials!")
        logger.error(
            "Please ensure MAGICKMIND_EMAIL and MAGICKMIND_PASSWORD are set in your .env file"
        )
        return

    if not ws_endpoint:
        logger.warning("WARNING: MAGICKMIND_WS_ENDPOINT is not set!")
        logger.warning(
            "Realtime examples will fail without it. Please add MAGICKMIND_WS_ENDPOINT to your .env file."
        )

    # Initialize client — auth is lazy (happens on first API call)
    async with MagickMind(email=email, password=password, base_url=base_url) as client:
        await _setup(client)


async def _setup(client: MagickMind):
    updates = {}

    # 2. Setup End User
    logger.info("\n--- 1. End User ---")
    user_id = os.getenv("USER_ID")
    if not user_id:
        user_id = "user-test-456"
        logger.info(f"USER_ID not set. Using default: {user_id}")
        updates["USER_ID"] = user_id
    else:
        logger.info(f"Using existing USER_ID: {user_id}")

    try:
        # Create/Verify EndUser
        await client.v1.end_user.create(
            name="Test User",
            external_id=user_id,
        )
        logger.info(f"EndUser verified: {user_id}")
    except ValidationError as e:
        # Handle field-level validation errors
        logger.warning(f"EndUser validation issue: {e.title}")
        for field, messages in e.get_field_errors().items():
            logger.warning(f"  - {field}: {', '.join(messages)}")
    except ProblemDetailsException as e:
        # Handle other API errors (e.g., user already exists)
        if e.status == 409:  # Conflict - already exists
            logger.info(f"EndUser already exists: {user_id}")
        else:
            logger.warning(f"Note on EndUser: [{e.status}] {e.title}: {e.detail}")

    # 3. Setup Project
    logger.info("\n--- 2. Project ---")
    project_id = os.getenv("PROJECT_ID")
    if project_id:
        logger.info(f"Using existing PROJECT_ID: {project_id}")
    else:
        logger.info("PROJECT_ID not set. Searching/Creating...")
        try:
            projects = await client.v1.project.list()
            if projects:
                project_id = projects[0].id
                logger.info(
                    f"Found existing Project: {project_id} ({projects[0].name})"
                )
            else:
                # create() returns Project directly (not wrapped)
                project = await client.v1.project.create(
                    name="Test Project", description="Created by SDK Setup"
                )
                project_id = project.id
                logger.info(f"Created new Project: {project_id}")

            updates["PROJECT_ID"] = project_id

        except ValidationError as e:
            logger.error(f"Project validation error: {e.title}")
            for field, messages in e.get_field_errors().items():
                logger.error(f"  - {field}: {', '.join(messages)}")
            return
        except ProblemDetailsException as e:
            logger.error(f"Failed to setup Project: [{e.status}] {e.detail}")
            if e.request_id:
                logger.error(f"  Request ID: {e.request_id}")
            return
        except RateLimitError:
            logger.error("Rate limited! Please wait and try again.")
            return

    # 4. Setup Mindspace
    logger.info("\n--- 3. Mindspace ---")
    mindspace_id = os.getenv("MINDSPACE_ID")
    # Don't use the dummy default from some example .env files if it's invalid
    if mindspace_id == "mind-test-123":
        mindspace_id = None

    if mindspace_id:
        logger.info(f"Using existing MINDSPACE_ID: {mindspace_id}")
    else:
        logger.info("MINDSPACE_ID not set (or is dummy). Searching/Creating...")
        try:
            # Test mindspace.list() with the new pagination format
            logger.info(f"Listing mindspaces for user: {user_id}")
            mindspace_list = await client.v1.mindspace.list(participant_id=user_id)

            # Test new data+paging structure
            logger.info(f"  Found {len(mindspace_list.data)} mindspace(s)")
            if mindspace_list.paging:
                logger.info(f"  has_more: {mindspace_list.paging.has_more}")

            # Use existing mindspace if found, otherwise create one
            if mindspace_list.data:
                mindspace = mindspace_list.data[0]
                mindspace_id = mindspace.id
                logger.info(f"  Using existing: {mindspace.name} ({mindspace_id})")
                updates["MINDSPACE_ID"] = mindspace_id
            else:
                # create() returns MindSpace directly (not wrapped)
                mindspace = await client.v1.mindspace.create(
                    name="Test Mindspace",
                    type="PRIVATE",
                    description="Realtime Test Mindspace",
                    project_id=project_id,
                    participant_ids=[user_id],
                )
                mindspace_id = mindspace.id
                logger.info(f"Created new Mindspace: {mindspace_id}")
                updates["MINDSPACE_ID"] = mindspace_id

        except ValidationError as e:
            logger.error(f"Mindspace validation error: {e.title}")
            for field, messages in e.get_field_errors().items():
                logger.error(f"  - {field}: {', '.join(messages)}")
            return
        except ProblemDetailsException as e:
            logger.error(f"Failed to setup Mindspace: [{e.status}] {e.detail}")
            if e.request_id:
                logger.error(f"  Request ID: {e.request_id}")
            return

    # 5. Populate .env
    if updates:
        update_env_file(updates)
        logger.info("\n.env file updated successfully!")
    else:
        logger.info("\nEnvironment is already fully configured.")

    logger.info("=" * 60)
    logger.info("READY TO RUN EXAMPLES")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
