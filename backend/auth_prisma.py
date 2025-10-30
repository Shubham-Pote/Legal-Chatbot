"""
Authentication system using Prisma + PostgreSQL and JWT tokens
"""
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from prisma import Prisma
from typing import Optional, Tuple, Dict

load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Initialize Prisma client
db = Prisma()

async def connect_db():
    """Connect to database"""
    if not db.is_connected():
        await db.connect()

async def disconnect_db():
    """Disconnect from database"""
    if db.is_connected():
        await db.disconnect()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_jwt_token(user_id: int, email: str) -> str:
    """Create a JWT token for a user"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def signup_user(email: str, password: str, name: str) -> Tuple[bool, str, Optional[str]]:
    """
    Register a new user

    Returns:
        (success, message, token)
    """
    try:
        await connect_db()

        # Check if user already exists
        existing_user = await db.user.find_unique(where={"email": email})
        if existing_user:
            return False, "User with this email already exists", None

        # Create new user
        password_hash = hash_password(password)
        user = await db.user.create(
            data={
                "email": email,
                "name": name,
                "passwordHash": password_hash
            }
        )

        # Generate JWT token
        token = create_jwt_token(user.id, user.email)

        return True, "User created successfully", token

    except Exception as e:
        return False, f"Error creating user: {str(e)}", None

async def login_user(email: str, password: str) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
    """
    Authenticate a user

    Returns:
        (success, message, token, user_data)
    """
    try:
        await connect_db()

        # Find user by email
        user = await db.user.find_unique(where={"email": email})

        if not user:
            return False, "User not found", None, None

        # Verify password
        if not verify_password(password, user.passwordHash):
            return False, "Invalid password", None, None

        # Generate JWT token
        token = create_jwt_token(user.id, user.email)

        # Return user data (without password hash)
        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.createdAt.isoformat()
        }

        return True, "Login successful", token, user_data

    except Exception as e:
        return False, f"Error during login: {str(e)}", None, None

async def get_user_from_token(token: str) -> Optional[Dict]:
    """Get user data from JWT token"""
    try:
        payload = verify_jwt_token(token)
        if not payload:
            return None

        await connect_db()
        user = await db.user.find_unique(where={"id": payload["user_id"]})

        if not user:
            return None

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.createdAt.isoformat()
        }
    except Exception:
        return None

async def save_conversation(user_id: int, query: str, response: str, sources: list) -> Tuple[bool, Optional[int]]:
    """
    Save a conversation with messages

    Returns:
        (success, conversation_id)
    """
    try:
        await connect_db()

        # Create or get today's conversation
        conversation = await db.conversation.create(
            data={
                "userId": user_id,
                "title": query[:100]  # Use first 100 chars of query as title
            }
        )

        # Save user message
        await db.message.create(
            data={
                "conversationId": conversation.id,
                "role": "user",
                "content": query
            }
        )

        # Save assistant message
        await db.message.create(
            data={
                "conversationId": conversation.id,
                "role": "assistant",
                "content": response,
                "sources": sources
            }
        )

        return True, conversation.id

    except Exception as e:
        print(f"Error saving conversation: {e}")
        return False, None

async def get_user_conversations(user_id: int, limit: int = 10):
    """Get user's recent conversations"""
    try:
        await connect_db()

        conversations = await db.conversation.find_many(
            where={"userId": user_id},
            include={"messages": True},
            order={"createdAt": "desc"},
            take=limit
        )

        return conversations

    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return []

async def update_message_rating(message_id: int, rating: str) -> bool:
    """Update rating for a message"""
    try:
        await connect_db()

        await db.message.update(
            where={"id": message_id},
            data={"rating": rating}
        )

        return True

    except Exception as e:
        print(f"Error updating rating: {e}")
        return False

async def get_chat_history(user_id: int) -> list:
    """Get formatted chat history for display"""
    try:
        conversations = await get_user_conversations(user_id, limit=1)

        if not conversations:
            return []

        # Get messages from latest conversation
        messages = conversations[0].messages

        chat_history = []
        for i in range(0, len(messages), 2):  # Process in pairs (user + assistant)
            if i + 1 < len(messages):
                user_msg = messages[i]
                assistant_msg = messages[i + 1]

                chat_history.append({
                    "message_id": assistant_msg.id,
                    "query": user_msg.content,
                    "response": assistant_msg.content,
                    "sources": assistant_msg.sources or [],
                    "rating": assistant_msg.rating,
                    "timestamp": user_msg.createdAt.isoformat()
                })

        return chat_history

    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []

