import os
import logging
from typing import Dict
from dotenv import load_dotenv, set_key
from magick_mind import MagickMind

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


def main():
    logger.info("=" * 60)
    logger.info("🛠️  SDK RESOURCE SETUP")
    logger.info("=" * 60)

    # 1. Validate Credentials
    email = os.getenv("BIFROST_EMAIL")
    password = os.getenv("BIFROST_PASSWORD")
    base_url = os.getenv("BIFROST_BASE_URL", "https://dev-bifrost.magickmind.ai")
    ws_endpoint = os.getenv("BIFROST_WS_ENDPOINT")

    if not email or not password:
        logger.error("❌ ERROR: Missing credentials!")
        logger.error(
            "Please ensure BIFROST_EMAIL and BIFROST_PASSWORD are set in your .env file"
        )
        return

    if not ws_endpoint:
        logger.warning("⚠️  WARNING: BIFROST_WS_ENDPOINT is not set!")
        logger.warning(
            "Realtime examples will fail without it. Please add it to your .env file."
        )

    client = MagickMind(email=email, password=password, base_url=base_url)
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
        client.v1.end_user.create(
            name="Test User",
            tenant_id="tenant-test-1",
            actor_id="actor-test-1",
            external_id=user_id,
        )
        logger.info(f"✅ EndUser verified: {user_id}")
    except Exception as e:
        logger.warning(f"ℹ️  Note on EndUser: {e}")

    # 3. Setup Project
    logger.info("\n--- 2. Project ---")
    project_id = os.getenv("PROJECT_ID")
    if project_id:
        logger.info(f"Using existing PROJECT_ID: {project_id}")
    else:
        logger.info("PROJECT_ID not set. Searching/Creating...")
        try:
            projects = client.v1.project.list()
            if projects:
                project_id = projects[0].id
                logger.info(
                    f"✅ Found existing Project: {project_id} ({projects[0].name})"
                )
            else:
                resp = client.v1.project.create(
                    name="Test Project", description="Created by SDK Setup"
                )
                project_id = resp.id
                logger.info(f"✅ Created new Project: {project_id}")

            updates["PROJECT_ID"] = project_id
        except Exception as e:
            logger.error(f"❌ Failed to setup Project: {e}")
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
        logger.info("MINDSPACE_ID not set (or is dummy). Creating...")
        try:
            resp = client.v1.mindspace.create(
                name="Test Mindspace",
                type="PRIVATE",
                description="Realtime Test Mindspace",
                project_id=project_id,
                user_ids=[user_id],
            )
            mindspace_id = resp.mindspace.id
            logger.info(f"✅ Created new Mindspace: {mindspace_id}")
            updates["MINDSPACE_ID"] = mindspace_id
        except Exception as e:
            logger.error(f"❌ Failed to setup Mindspace: {e}")
            return

    # 5. Populate .env
    if updates:
        update_env_file(updates)
        logger.info("\n✨ .env file updated successfully!")
    else:
        logger.info("\n✨ Environment is already fully configured.")

    logger.info("=" * 60)
    logger.info("READY TO RUN EXAMPLES")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
