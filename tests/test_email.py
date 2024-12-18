""" Tests for email service. """

import pytest
from app.services.email_service import EmailService
from app.utils.template_manager import TemplateManager
from app.models.user_model import User


@pytest.mark.asyncio
async def test_send_markdown_email(email_service):
    """Test sending a markdown email."""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "verification_url": "http://example.com/verify?token=abc123",
    }
    await email_service.send_user_email(user_data, "email_verification")
    # Manual verification in Mailtrap


@pytest.mark.asyncio
async def test_send_professional_status_update_email(email_service):
    """Test sending a professional status update email."""
    # Mock user data
    user = User(
        first_name="Test",
        email="test@example.com",
        is_professional=True,  # Test case where status is Professional
    )

    await email_service.send_professional_status_update_email(user)
