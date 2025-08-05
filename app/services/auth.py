from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.mongodb import get_database
from app.schemas.user import UserCreate, UserInDB, UserResponse, UserLogin
from app.utils.security import get_password_hash, verify_password, verify_token
from datetime import datetime

security = HTTPBearer()

class AuthService:
    def __init__(self):
        pass
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        db = await get_database()
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        user_dict = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Insert user
        result = await db.users.insert_one(user_dict)
        
        # Return user response
        return UserResponse(
            id=str(result.inserted_id),
            email=user_data.email,
            created_at=user_dict["created_at"],
            is_active=True
        )
    
    async def authenticate_user(self, user_login: UserLogin) -> Optional[UserInDB]:
        """Authenticate user login"""
        db = await get_database()
        
        # Find user by email
        user_doc = await db.users.find_one({"email": user_login.email})
        if not user_doc:
            return None
        
        # Verify password
        if not verify_password(user_login.password, user_doc["hashed_password"]):
            return None
        
        # Return user object
        return UserInDB(**user_doc)
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        db = await get_database()
        user_doc = await db.users.find_one({"email": email})
        if user_doc:
            return UserInDB(**user_doc)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        db = await get_database()
        from bson import ObjectId
        try:
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return UserInDB(**user_doc)
        except:
            pass
        return None

auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get current authenticated user"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token
        token = credentials.credentials
        
        # Verify token and get email
        email = verify_token(token)
        if email is None:
            raise credentials_exception
        
        # Get user from database
        user = await auth_service.get_user_by_email(email)
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception:
        raise credentials_exception

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
