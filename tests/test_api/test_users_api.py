"""Tests for the users API endpoints."""

from builtins import str
import pytest
from httpx import AsyncClient
from urllib.parse import urlencode
from app.main import app
from app.models.user_model import User, UserRole
from app.utils.nickname_gen import generate_nickname
from app.utils.security import hash_password
from app.services.jwt_service import decode_token  # Import your FastAPI app


# Example of a test function using the async_client fixture
@pytest.mark.asyncio
async def test_create_user_access_denied(async_client, user_token, email_service):
    """Test that a regular user cannot create a new user."""
    headers = {"Authorization": f"Bearer {user_token}"}
    # Define user data for the test
    user_data = {
        "nickname": generate_nickname(),
        "email": "test@example.com",
        "password": "sS#fdasrongPassword123!",
    }
    # Send a POST request to create a user
    response = await async_client.post("/users/", json=user_data, headers=headers)
    # Asserts
    assert response.status_code == 403


# You can similarly refactor other test functions to use the async_client fixture
@pytest.mark.asyncio
async def test_retrieve_user_access_denied(async_client, verified_user, user_token):
    """Test that a regular user cannot retrieve another user's data."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get(f"/users/{verified_user.id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_user_access_allowed(async_client, admin_user, admin_token):
    """Test that an admin user can retrieve another user's data."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(admin_user.id)


@pytest.mark.asyncio
async def test_update_user_email_access_denied(async_client, verified_user, user_token):
    """Test that a regular user cannot update another user's email."""
    updated_data = {"email": f"updated_{verified_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.put(
        f"/users/{verified_user.id}", json=updated_data, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_email_access_allowed(async_client, admin_user, admin_token):
    """Test that an admin user can update another user's email."""
    updated_data = {"email": f"updated_{admin_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(
        f"/users/{admin_user.id}", json=updated_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == updated_data["email"]


@pytest.mark.asyncio
async def test_delete_user(async_client, admin_user, admin_token):
    """Test that an admin user can delete another user."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_response = await async_client.delete(
        f"/users/{admin_user.id}", headers=headers
    )
    assert delete_response.status_code == 204
    # Verify the user is deleted
    fetch_response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert fetch_response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client, verified_user):
    """Test creating a user with an email that already exists."""
    user_data = {
        "email": verified_user.email,
        "password": "AnotherPassword123!",
        "role": UserRole.ADMIN.name,
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400
    assert "Email already exists" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client):
    """Test creating a user with an invalid email."""
    user_data = {
        "email": "notanemail",
        "password": "ValidPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client, verified_user):
    """Test successful login with valid credentials."""
    # Attempt to login with the test user
    form_data = {"username": verified_user.email, "password": "MySuperPassword$1234"}
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Check for successful login response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Use the decode_token method from jwt_service to decode the JWT
    decoded_token = decode_token(data["access_token"])
    assert decoded_token is not None, "Failed to decode token"
    assert (
        decoded_token["role"] == "AUTHENTICATED"
    ), "The user role should be AUTHENTICATED"


@pytest.mark.asyncio
async def test_login_user_not_found(async_client):
    """Test login with a user that does not exist."""
    form_data = {
        "username": "nonexistentuser@here.edu",
        "password": "DoesNotMatter123!",
    }
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_incorrect_password(async_client, verified_user):
    """Test login with incorrect password."""
    form_data = {"username": verified_user.email, "password": "IncorrectPassword123!"}
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_unverified_user(async_client, unverified_user):
    """Test login with an unverified user."""
    form_data = {"username": unverified_user.email, "password": "MySuperPassword$1234"}
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_locked_user(async_client, locked_user):
    """Test login with a locked user."""
    form_data = {"username": locked_user.email, "password": "MySuperPassword$1234"}
    response = await async_client.post(
        "/login/",
        data=urlencode(form_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 400
    assert (
        "Account locked due to too many failed login attempts."
        in response.json().get("detail", "")
    )


@pytest.mark.asyncio
async def test_delete_user_does_not_exist(async_client, admin_token):
    """Test deleting a user that does not exist."""
    non_existent_user_id = "00000000-0000-0000-0000-000000000000"  # Valid UUID format
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_response = await async_client.delete(
        f"/users/{non_existent_user_id}", headers=headers
    )
    assert delete_response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_github(async_client, admin_user, admin_token):
    """Test updating a user's GitHub profile URL."""
    updated_data = {"github_profile_url": "http://www.github.com/kaw393939"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(
        f"/users/{admin_user.id}", json=updated_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["github_profile_url"] == updated_data["github_profile_url"]


@pytest.mark.asyncio
async def test_update_user_linkedin(async_client, admin_user, admin_token):
    """Test updating a user's LinkedIn profile URL."""
    updated_data = {"linkedin_profile_url": "http://www.linkedin.com/kaw393939"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(
        f"/users/{admin_user.id}", json=updated_data, headers=headers
    )
    assert response.status_code == 200
    assert (
        response.json()["linkedin_profile_url"] == updated_data["linkedin_profile_url"]
    )


@pytest.mark.asyncio
async def test_list_users_as_admin(async_client, admin_token):
    """Test listing users as an admin."""
    response = await async_client.get(
        "/users/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_list_users_as_manager(async_client, manager_token):
    """Test listing users as a manager."""
    response = await async_client.get(
        "/users/", headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_users_unauthorized(async_client, user_token):
    """Test listing users as a regular user."""
    response = await async_client.get(
        "/users/", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403  # Forbidden, as expected for regular user


@pytest.mark.asyncio
async def test_update_profile_success(async_client, user_token):
    """Test updating profile for an authenticated user."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "first_name": "UpdatedFirstName",
        "bio": "Updated bio for the user.",
    }
    response = await async_client.put(
        "/profile",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["first_name"] == "UpdatedFirstName"
    assert json_response["bio"] == "Updated bio for the user."


@pytest.mark.asyncio
async def test_update_profile_missing_auth(async_client):
    """Test updating profile without authentication."""
    payload = {"first_name": "UpdatedFirstName", "bio": "Updated bio for the user."}
    response = await async_client.put("/profile", json=payload)
    assert response.status_code == 401  # Unauthorized
    assert "Not authenticated" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_update_profile_invalid_data(async_client, user_token):
    """Test updating profile with invalid data."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {}  # No valid fields provided
    response = await async_client.put(
        "/profile",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 422  # Unprocessable Entity
    assert "value_error" in response.json()["detail"][0]["type"]


@pytest.fixture
def fake_token():
    """Return a fake token for testing."""
    return "fake_token"


@pytest.mark.asyncio
async def test_update_profile_user_not_found(async_client, fake_token):
    """Test updating profile for a non-existent user."""

    headers = {"Authorization": f"Bearer {fake_token}"}
    payload = {
        "first_name": "NonExistentUser",
        "bio": "This user does not exist anymore.",
    }
    response = await async_client.put(
        "/profile",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 401  # Unauthorized
