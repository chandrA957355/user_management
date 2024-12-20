from builtins import str
from datetime import datetime
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user_model import User, UserRole
from app.services.user_service import UserService
from app.utils.nickname_gen import generate_nickname
from app.utils.security import hash_password
from app.services.jwt_service import decode_token
from tests.conftest import admin_user  # Import your FastAPI app

# Example of a test function using the async_client fixture
@pytest.mark.asyncio
async def test_create_user_access_denied(async_client, user_token, email_service):
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
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get(f"/users/{verified_user.id}", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_retrieve_user_access_allowed(async_client, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(admin_user.id)

@pytest.mark.asyncio
async def test_update_user_email_access_denied(async_client, verified_user, user_token):
    updated_data = {"email": f"updated_{verified_user.id}@example.com"}
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.put(f"/users/{verified_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_user_email_access_allowed(async_client, admin_user, admin_token):
    updated_data = {"email": f"updated_{admin_user.id}@example.com", "nickname": "new_nickname"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == updated_data["email"]


@pytest.mark.asyncio
async def test_delete_user(async_client, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_response = await async_client.delete(f"/users/{admin_user.id}", headers=headers)
    assert delete_response.status_code == 204
    # Verify the user is deleted
    fetch_response = await async_client.get(f"/users/{admin_user.id}", headers=headers)
    assert fetch_response.status_code == 404

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "AnotherPassword123!",
        "role": UserRole.ADMIN.name
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400
    assert "Email already exists" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client):
    user_data = {
        "email": "notanemail",
        "password": "ValidPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422

import pytest
from app.services.jwt_service import decode_token
from urllib.parse import urlencode

@pytest.mark.asyncio
async def test_login_success(async_client, verified_user):
    # Attempt to login with the test user
    form_data = {
        "username": verified_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    # Check for successful login response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Use the decode_token method from jwt_service to decode the JWT
    decoded_token = decode_token(data["access_token"])
    assert decoded_token is not None, "Failed to decode token"
    assert decoded_token["role"] == "AUTHENTICATED", "The user role should be AUTHENTICATED"

@pytest.mark.asyncio
async def test_login_user_not_found(async_client):
    form_data = {
        "username": "nonexistentuser@here.edu",
        "password": "DoesNotMatter123!"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_incorrect_password(async_client, verified_user):
    form_data = {
        "username": verified_user.email,
        "password": "IncorrectPassword123!"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 401
    assert "Incorrect email or password." in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_unverified_user(async_client, unverified_user):
    form_data = {
        "username": unverified_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_locked_user(async_client, locked_user):
    form_data = {
        "username": locked_user.email,
        "password": "MySuperPassword$1234"
    }
    response = await async_client.post("/login/", data=urlencode(form_data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 400
    assert "Account locked due to too many failed login attempts." in response.json().get("detail", "")
@pytest.mark.asyncio
async def test_delete_user_does_not_exist(async_client, admin_token):
    non_existent_user_id = "00000000-0000-0000-0000-000000000000"  # Valid UUID format
    headers = {"Authorization": f"Bearer {admin_token}"}
    delete_response = await async_client.delete(f"/users/{non_existent_user_id}", headers=headers)
    assert delete_response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_github(async_client, test_user, admin_token, db_session):
    unique_email = f"{datetime.now().timestamp()}_{test_user.email}"
    updated_data = {"email": unique_email, "github_profile_url": "http://www.github.com/kaw393939", "nickname": "UpdatedNickname"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    pre_update = await async_client.get(f"/users/{test_user.id}", headers=headers)
    print("Pre-Update User Data:", pre_update.json())

    result = await db_session.execute(sa.select(User).where(User.id == test_user.id))
    db_user = result.scalars().first()
    if db_user:
        print("Database User Check: User found")
    else:
        print("Database User Check: User NOT found")

    response = await async_client.put(f"/users/{test_user.id}", json=updated_data, headers=headers)
    print("Update Response:", response.json())

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code} with message {response.text}"

    post_update = await async_client.get(f"/users/{test_user.id}", headers=headers)
    print("Post-Update User Data:", post_update.json())

@pytest.mark.asyncio
async def test_update_user_missing_fields(async_client, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json={}, headers=headers)
    assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_update_user_linkedin(async_client, admin_user, admin_token):
    unique_email = f"{datetime.now().timestamp()}_{admin_user.email}"
    updated_data = {"email": unique_email, "linkedin_profile_url": "http://www.linkedin.com/kaw393939", "nickname": "UpdatedNickname"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["linkedin_profile_url"] == updated_data["linkedin_profile_url"]

@pytest.mark.asyncio
async def test_list_users_as_admin(async_client, admin_token):
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert 'items' in response.json()

@pytest.mark.asyncio
async def test_list_users_as_manager(async_client, manager_token):
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_list_users_unauthorized(async_client, user_token):
    response = await async_client.get(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403  # Forbidden, as expected for regular user

@pytest.mark.asyncio
async def test_search_users_by_email(async_client: AsyncClient, db_session, admin_token, mock_email_service):
    """
    Test searching for a user by their email address.
    """
    # Arrange: Create a user with a specific email
    user_data = {
        "nickname": "emailuser",
        "email": "emailsearch@example.com",
        "password": "SecurePassword123!",
        "role": "AUTHENTICATED"
    }
    created_user = await UserService.create(db_session, user_data, mock_email_service)

    # Act: Perform a search query by email
    response = await async_client.get(
        "/users/search/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"email": created_user.email}
    )

    # Assert: Verify that the correct user is returned
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["email"] == created_user.email
    assert response_data["items"][0]["nickname"] == created_user.nickname


@pytest.mark.asyncio
async def test_search_users_by_role(async_client: AsyncClient, db_session, admin_token, mock_email_service):
    """
    Test searching for users by their role.
    """
    # Arrange: Create users with different roles
    admin_user = {
        "nickname": "admin_user",
        "email": "admin@example.com",
        "password": "SecurePassword123!",
        "role": "ADMIN"
    }
    auth_user = {
        "nickname": "authuser",
        "email": "authrole@example.com",
        "password": "SecurePassword123!",
        "role": "AUTHENTICATED"
    }
    await UserService.create(db_session, admin_user, mock_email_service)
    await UserService.create(db_session, auth_user, mock_email_service)

    # Act: Search for users with the ADMIN role
    response = await async_client.get(
        "/users/search/",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"role": "ADMIN"}
    )

    # Assert: Verify only the ADMIN user is returned
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["role"] == "ADMIN"
    assert response_data["items"][0]["email"] == admin_user["email"]
    assert response_data["items"][0]["nickname"] == admin_user["nickname"]
