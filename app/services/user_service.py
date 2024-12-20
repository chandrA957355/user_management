from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone
import secrets
from typing import Optional, Dict, List
from pydantic import ValidationError
from sqlalchemy import func, null, update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_email_service, get_settings
from app.models.user_model import User
from app.schemas.user_schemas import UserCreate, UserResponse, UserUpdate
from app.utils.nickname_gen import generate_nickname
from app.utils.security import generate_verification_token, hash_password, verify_password
from uuid import UUID
from app.services.email_service import EmailService
from app.models.user_model import UserRole
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            validated_data = UserCreate(**user_data).model_dump()
            
            # Check for duplicate email
            if await cls.get_by_email(session, validated_data['email']):
                raise ValueError("User with given email already exists.")
            
            # Check for duplicate nickname
            if await cls.get_by_nickname(session, validated_data['nickname']):
                raise ValueError("User with given nickname already exists.")

            validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            new_user = User(**validated_data)

            session.add(new_user)
            await session.commit()
            return new_user
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None
        except ValueError as e:
            logger.error(e)
            return None

    @classmethod
    async def update(cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]) -> Optional[User]:
        try:
            validated_data = UserUpdate(**update_data).model_dump(exclude_unset=True)

            if 'email' in validated_data:
                existing_user = await cls.get_by_email(session, validated_data['email'])
                if existing_user and existing_user.id != user_id:
                    logger.error("User with given email already exists.")
                    return None

            if 'nickname' in validated_data:
                existing_user_nickname = await cls.get_by_nickname(session, validated_data['nickname'])
                if existing_user_nickname and existing_user_nickname.id != user_id:
                    logger.error("User with given nickname already exists.")
                    return None
                
            if 'password' in validated_data:
                validated_data['hashed_password'] = hash_password(validated_data.pop('password'))

            query = (
                update(User)
                .where(User.id == user_id)
                .values(**validated_data)
                .execution_options(synchronize_session="fetch")
            )
            await cls._execute_query(session, query)

            updated_user = await cls.get_by_id(session, user_id)
            if updated_user:
                session.refresh(updated_user)
                logger.info(f"User {user_id} updated successfully.")
                return updated_user

            logger.error(f"User {user_id} not found after update attempt.")
            return None
        except Exception as e:
            logger.error(f"Error during user update: {e}")
            return None
        
    @classmethod
    async def search_users(
        cls,
        session: AsyncSession,
        username: Optional[str] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[str] = None,
        account_status: Optional[str] = None,
        registration_date_from: Optional[datetime] = None,
        registration_date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[UserResponse]:
        """
        Searches for users in the database based on provided filters. Supports filtering by username, email, 
        name, role, account status, and registration date range. Includes pagination.

        :param session: Active database session.
        :param username: Filter by username (case-insensitive).
        :param email: Filter by email (case-insensitive).
        :param first_name: Filter by first name (case-insensitive).
        :param last_name: Filter by last name (case-insensitive).
        :param role: Filter by user role.
        :param account_status: "active" or "locked" to filter by account status.
        :param registration_date_from: Start date for registration date range filter.
        :param registration_date_to: End date for registration date range filter.
        :param skip: Number of records to skip for pagination.
        :param limit: Maximum number of records to return for pagination.
        :return: List of UserResponse objects matching the filters.
        """
        query = select(User)

        # Create filters dynamically
        if username:
            query = query.filter(func.lower(User.nickname) == func.lower(username))
        if email:
            query = query.filter(func.lower(User.email) == func.lower(email))
        if first_name:
            query = query.filter(func.lower(User.first_name) == func.lower(first_name))
        if last_name:
            query = query.filter(func.lower(User.last_name) == func.lower(last_name))
        if role:
            query = query.filter(User.role == role)
        if account_status:
            is_locked = account_status.lower() == "locked"
            query = query.filter(User.is_locked == is_locked)
        if registration_date_from:
            query = query.filter(User.created_at >= registration_date_from)
        if registration_date_to:
            query = query.filter(User.created_at <= registration_date_to)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute the query
        result = await cls._execute_query(session, query)
        users = result.scalars().all() if result else []

        # Map to response schema
        user_responses = [
            UserResponse(
                id=user.id,
                email=user.email,
                nickname=user.nickname,
                is_professional=user.is_professional,
                role=user.role,
                registration_date=user.created_at,
                account_status="Active" if not user.is_locked else "Locked"
            )
            for user in users
        ]

        return user_responses

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.info(f"User with ID {user_id} not found.")
            return False
        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def list_users(cls, session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await cls._execute_query(session, query)
        return result.scalars().all() if result else []

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str], get_email_service) -> Optional[User]:
        return await cls.create(session, user_data, get_email_service)
    

    @classmethod
    async def login_user(cls, session: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await cls.get_by_email(session, email)
        if user:
            if user.email_verified is False:
                return None
            if user.is_locked:
                return None
            if verify_password(password, user.hashed_password):
                user.failed_login_attempts = 0
                user.last_login_at = datetime.now(timezone.utc)
                session.add(user)
                await session.commit()
                return user
            else:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= settings.max_login_attempts:
                    user.is_locked = True
                session.add(user)
                await session.commit()
        return None

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False


    @classmethod
    async def reset_password(cls, session: AsyncSession, user_id: UUID, new_password: str) -> bool:
        hashed_password = hash_password(new_password)
        user = await cls.get_by_id(session, user_id)
        if user:
            user.hashed_password = hashed_password
            user.failed_login_attempts = 0  # Resetting failed login attempts
            user.is_locked = False  # Unlocking the user account, if locked
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def verify_email_with_token(cls, session: AsyncSession, user_id: UUID, token: str) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user:
            if user.email_verified: 
                return False
            if user.verification_token == token:
                user.email_verified = True
                user.verification_token = None 
                user.role = UserRole.AUTHENTICATED if user.role == UserRole.ANONYMOUS else user.role
                session.add(user)
                await session.commit()
                return True
        return False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """
        Count the number of users in the database.

        :param session: The AsyncSession instance for database access.
        :return: The count of users.
        """
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        count = result.scalar()
        return count
    
    @classmethod
    async def unlock_user_account(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.is_locked:
            user.is_locked = False
            user.failed_login_attempts = 0  # Optionally reset failed login attempts
            session.add(user)
            await session.commit()
            return True
        return False
