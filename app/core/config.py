import os
from pathlib import Path
from typing import List

from starlette.config import Config
from typing import List
from starlette.datastructures import CommaSeparatedStrings



VERSION = "0.0.1"
ROOT_PATH = Path(__file__).parent.parent.parent
env_file = os.environ.get("ENV_FILE") if "ENV_FILE" in os.environ else os.path.join(ROOT_PATH, ".env")

config = Config(env_file)

# ======= DATABASE ==========

MONGODB_URL: str = config("MONGODB_URL", default="mongodb://localhost:27017/")
MONGO_DATABASE: str = config("MONGO_DATABASE", default="clean-database")
MONGODB_MAX_CONNECTIONS_COUNT: int = config("MONGODB_MAX_CONNECTIONS_COUNT", cast=int, default=20)
MONGODB_MIN_CONNECTIONS_COUNT: int = config("MONGODB_MIN_CONNECTIONS_COUNT", cast=int, default=1)

MONGO_COLLECTION_USERS: str = config("MONGO_COLLECTION_USERS", default="user-collection")
MONGO_COLLECTION_ROLES: str = config("MONGO_COLLECTION_ROLES", default="role-collection")
MONGO_COLLECTION_PERMISSIONS: str = config("MONGO_COLLECTION_PERMISSIONS", default="permission-collection")
MONGO_COLLECTION_USER_ROLES: str = config("MONGO_COLLECTION_USER_ROLES", default="user-role-collection")
MONGO_COLLECTION_STUDENT_PROFILES: str = config("MONGO_COLLECTION_STUDENT_PROFILES", default="student-profiles")


# =========== PROJECT ==========
PROJECT_NAME: str = config("PROJECT_NAME", default="Api")
DEBUG: bool = config("DEBUG", cast=bool, default=False)
UNIT_TEST = config("UNIT_TEST", cast=bool, default=False)
DEPLOYMENT_ENV: str = config("DEPLOYMENT_ENV", default="local")
ALLOWED_HOSTS: List[str] = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings, default="*")
AIO_CLIENT_TOUT_SEC: int = config("AIO_CLIENT_TOUT_SEC", cast=int, default=10)


# =========== SECURITY ==========
SECRET_KEY = config("SECRET_KEY")
ALGORITHM: str = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=30)
# ======= AWS S3 Configuration =======
AWS_ACCESS_KEY_ID: str = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY: str = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_REGION: str = config("AWS_REGION", default="us-east-1")
S3_BUCKET_NAME: str = config("S3_BUCKET_NAME", default="student-uploads")
S3_UPLOAD_ENABLED: bool = config("S3_UPLOAD_ENABLED", cast=bool, default=False)
MAX_UPLOAD_SIZE: int = config("MAX_UPLOAD_SIZE", cast=int, default=10485760)  # 10MB in bytes
ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif"]
ALLOWED_DOCUMENT_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "txt"]

# ======= EMAIL Configuration =======
EMAIL_ENABLED: bool = config("EMAIL_ENABLED", cast=bool, default=False)
EMAIL_TEMPLATES_DIR: str = config("EMAIL_TEMPLATES_DIR", default="email_templates")
FROM_EMAIL: str = config("FROM_EMAIL", default="noreply@studentportal.com")
FROM_NAME: str = config("FROM_NAME", default="Student Portal")
DEFAULT_SMTP_PROVIDER: str = config("DEFAULT_SMTP_PROVIDER", default="gmail")

# SMTP Providers Configuration
SMTP_CONFIGS = {
    "gmail": {
        "host": config("GMAIL_SMTP_HOST", default="smtp.gmail.com"),
        "port": config("GMAIL_SMTP_PORT", cast=int, default=587),
        "username": config("GMAIL_USERNAME", default=""),
        "password": config("GMAIL_PASSWORD", default=""),
        "use_tls": True,
        "use_ssl": False,
    },
    "outlook": {
        "host": config("OUTLOOK_SMTP_HOST", default="smtp-mail.outlook.com"),
        "port": config("OUTLOOK_SMTP_PORT", cast=int, default=587),
        "username": config("OUTLOOK_USERNAME", default=""),
        "password": config("OUTLOOK_PASSWORD", default=""),
        "use_tls": True,
        "use_ssl": False,
    },
    "yahoo": {
        "host": config("YAHOO_SMTP_HOST", default="smtp.mail.yahoo.com"),
        "port": config("YAHOO_SMTP_PORT", cast=int, default=587),
        "username": config("YAHOO_USERNAME", default=""),
        "password": config("YAHOO_PASSWORD", default=""),
        "use_tls": True,
        "use_ssl": False,
    }
}

# ======= SMS Configuration =======
SMS_ENABLED: bool = config("SMS_ENABLED", cast=bool, default=False)
# ======= SMS Configuration =======
SMS_ENABLED: bool = config("SMS_ENABLED", cast=bool, default=False)
SMS_PROVIDER: str = config("SMS_PROVIDER", default="local")
DEFAULT_SMS_PROVIDER: str = config("DEFAULT_SMS_PROVIDER", default="twilio")
SMS_CONFIGS = {
    "twilio": {
        "account_sid": config("TWILIO_ACCOUNT_SID", default=""),
        "auth_token": config("TWILIO_AUTH_TOKEN", default=""),
        "from_number": config("TWILIO_FROM_NUMBER", default=""),
    },
    "aws_sns": {
        "aws_access_key_id": config("AWS_SNS_ACCESS_KEY_ID", default=""),
        "aws_secret_access_key": config("AWS_SNS_SECRET_ACCESS_KEY", default=""),
        "region": config("AWS_SNS_REGION", default="us-east-1"),
    },
    "nexmo": {
        "api_key": config("NEXMO_API_KEY", default=""),
        "api_secret": config("NEXMO_API_SECRET", default=""),
        "from_number": config("NEXMO_FROM_NUMBER", default=""),
    },
    "local": {
        "log_file": config("SMS_LOG_FILE", default="sms_log.txt"),
    }
}

# =========== AUTHORIZATION ==========
# Default system roles
DEFAULT_ADMIN_ROLE = "admin"
DEFAULT_USER_ROLE = "user"
DEFAULT_MODERATOR_ROLE = "moderator"
DEFAULT_STUDENT_ROLE = "student"

# Default permissions
DEFAULT_PERMISSIONS = [
    {"name": "read_users", "resource": "users", "action": "read", "description": "Read user information"},
    {"name": "write_users", "resource": "users", "action": "write", "description": "Create and update users"},
    {"name": "delete_users", "resource": "users", "action": "delete", "description": "Delete users"},
    {"name": "read_posts", "resource": "posts", "action": "read", "description": "Read posts"},
    {"name": "write_posts", "resource": "posts", "action": "write", "description": "Create and update posts"},
    {"name": "delete_posts", "resource": "posts", "action": "delete", "description": "Delete posts"},
    {"name": "manage_roles", "resource": "roles", "action": "manage", "description": "Manage user roles and permissions"},
    {"name": "read_admin", "resource": "admin", "action": "read", "description": "Access admin dashboard"},
    {"name": "manage_profile", "resource": "student_profile", "action": "manage", "description": "Manage student profile"},
    {"name": "upload_documents", "resource": "documents", "action": "upload", "description": "Upload documents and images"},
    {"name": "apply_colleges", "resource": "applications", "action": "apply", "description": "Apply to colleges"},
    {"name": "track_applications", "resource": "applications", "action": "read", "description": "Track application status"},
]