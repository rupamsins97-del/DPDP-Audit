import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Generator

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def ephemeral_clone(repository_url: str | None = None) -> Generator[str, None, None]:
    """Clones a repository into an ephemeral tmpfs directory with guaranteed cleanup (Invariant 2).

    Yields the local path of the cloned repository or a mock scaffold sandbox.
    Guarantees that shutil.rmtree is invoked on the temporary directory upon exit,
    even if an exception or unhandled error is raised during processing.
    """
    temp_dir = tempfile.mkdtemp(prefix="dpdp_repo_sandbox_")
    logger.info(f"[git_cloner] Initialized ephemeral sandbox at {temp_dir}")

    try:
        is_remote = repository_url and any(
            repository_url.startswith(prefix) for prefix in ("http://", "https://", "git@")
        )
        if is_remote and repository_url:
            logger.info(f"[git_cloner] Cloning shallow repository from {repository_url}...")
            try:
                # Run git shallow clone with a 30-second timeout
                subprocess.run(
                    ["git", "clone", "--depth", "1", repository_url, temp_dir],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
            except Exception as e:
                logger.warning(f"[git_cloner] Shallow clone failed or timed out: {e}")
        else:
            # If no repo URL or local test, scaffold sample application files in sandbox
            _scaffold_sample_sandbox(temp_dir)

        yield temp_dir
    finally:
        # Strict Invariant 2: Guaranteed purge on all exit paths
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"[git_cloner] Purged sandbox at {temp_dir} (Invariant 2 satisfied)")


def _scaffold_sample_sandbox(dir_path: str) -> None:
    """Scaffolds sample controllers and models for local testing and demonstration."""
    controllers_dir = os.path.join(dir_path, "app", "controllers")
    models_dir = os.path.join(dir_path, "app", "models")
    os.makedirs(controllers_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # Sample Python user controller with PII logging
    sample_py = """import logging
logger = logging.getLogger(__name__)

def login_user(user_email, user_phone, user_password):
    logger.info(f"User login attempt: {user_email}, phone: {user_phone}")
    return {"status": "success"}

def create_kyc_record(user_id, aadhaar_number, pan_number):
    logger.info(f"Submitting KYC with Aadhaar: {aadhaar_number} and PAN: {pan_number}")
    return {"status": "submitted"}
"""
    with open(os.path.join(controllers_dir, "user_controller.py"), "w", encoding="utf-8") as f:
        f.write(sample_py)

    # Sample JS auth handler with console.log PII
    sample_js = """function handleSignup(req, res) {
    const { email, phone, password } = req.body;
    console.log(`New user signup request with email: ${email} and phone: ${phone}`);
    return res.status(200).json({ success: true });
}
"""
    with open(os.path.join(controllers_dir, "auth_handler.js"), "w", encoding="utf-8") as f:
        f.write(sample_js)

    # Sample DB model
    sample_model = """from sqlalchemy import Column, Integer, String
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    aadhaar = Column(String, nullable=True) # Unencrypted PII
"""
    with open(os.path.join(models_dir, "user.py"), "w", encoding="utf-8") as f:
        f.write(sample_model)
