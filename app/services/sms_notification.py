from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.core.config import SMS_ENABLED, SMS_PROVIDER, SMS_CONFIGS

logger = logging.getLogger(__name__)


class SMSProvider(Enum):
    """Supported SMS providers"""
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"
    NEXMO = "nexmo"
    LOCAL = "local"  # For testing/development


@dataclass
class SMSMessage:
    """SMS message data"""
    phone_number: str
    message: str
    sender_id: Optional[str] = None
    
    def __post_init__(self):
        # Clean phone number (remove non-digits except +)
        self.phone_number = ''.join(c for c in self.phone_number if c.isdigit() or c == '+')


@dataclass
class SMSResponse:
    """SMS sending response"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    provider: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseSMSProvider(ABC):
    """Base class for SMS providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS message"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass


class TwilioSMSProvider(BaseSMSProvider):
    """Twilio SMS provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get("account_sid")
        self.auth_token = config.get("auth_token")
        self.from_number = config.get("from_number")
        
    def validate_config(self) -> bool:
        """Validate Twilio configuration"""
        return all([self.account_sid, self.auth_token, self.from_number])
    
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS via Twilio"""
        try:
            # Note: This is a placeholder implementation
            # In production, you would use the Twilio Python library:
            # from twilio.rest import Client
            # client = Client(self.account_sid, self.auth_token)
            # message = client.messages.create(
            #     body=message.message,
            #     from_=self.from_number,
            #     to=message.phone_number
            # )
            
            logger.info(f"[TWILIO] Would send SMS to {message.phone_number}: {message.message}")
            
            return SMSResponse(
                success=True,
                message_id=f"twilio_mock_{datetime.utcnow().timestamp()}",
                provider="twilio"
            )
            
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return SMSResponse(
                success=False,
                error_message=str(e),
                provider="twilio"
            )


class AWSSNSProvider(BaseSMSProvider):
    """AWS SNS SMS provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.aws_access_key_id = config.get("aws_access_key_id")
        self.aws_secret_access_key = config.get("aws_secret_access_key")
        self.region = config.get("region", "us-east-1")
        
    def validate_config(self) -> bool:
        """Validate AWS SNS configuration"""
        return all([self.aws_access_key_id, self.aws_secret_access_key])
    
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS via AWS SNS"""
        try:
            # Note: This is a placeholder implementation
            # In production, you would use the boto3 library:
            # import boto3
            # sns = boto3.client(
            #     'sns',
            #     aws_access_key_id=self.aws_access_key_id,
            #     aws_secret_access_key=self.aws_secret_access_key,
            #     region_name=self.region
            # )
            # response = sns.publish(
            #     PhoneNumber=message.phone_number,
            #     Message=message.message
            # )
            
            logger.info(f"[AWS SNS] Would send SMS to {message.phone_number}: {message.message}")
            
            return SMSResponse(
                success=True,
                message_id=f"aws_sns_mock_{datetime.utcnow().timestamp()}",
                provider="aws_sns"
            )
            
        except Exception as e:
            logger.error(f"AWS SNS SMS failed: {str(e)}")
            return SMSResponse(
                success=False,
                error_message=str(e),
                provider="aws_sns"
            )


class NexmoSMSProvider(BaseSMSProvider):
    """Nexmo (Vonage) SMS provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.from_number = config.get("from_number")
        
    def validate_config(self) -> bool:
        """Validate Nexmo configuration"""
        return all([self.api_key, self.api_secret, self.from_number])
    
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS via Nexmo"""
        try:
            # Note: This is a placeholder implementation
            # In production, you would use the Nexmo Python library:
            # import nexmo
            # client = nexmo.Client(key=self.api_key, secret=self.api_secret)
            # response = client.send_message({
            #     'from': self.from_number,
            #     'to': message.phone_number,
            #     'text': message.message
            # })
            
            logger.info(f"[NEXMO] Would send SMS to {message.phone_number}: {message.message}")
            
            return SMSResponse(
                success=True,
                message_id=f"nexmo_mock_{datetime.utcnow().timestamp()}",
                provider="nexmo"
            )
            
        except Exception as e:
            logger.error(f"Nexmo SMS failed: {str(e)}")
            return SMSResponse(
                success=False,
                error_message=str(e),
                provider="nexmo"
            )


class LocalSMSProvider(BaseSMSProvider):
    """Local SMS provider for testing/development"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_file = config.get("log_file", "sms_log.txt")
        
    def validate_config(self) -> bool:
        """Local provider is always valid"""
        return True
    
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Log SMS message locally"""
        try:
            log_entry = f"[{datetime.utcnow()}] SMS to {message.phone_number}: {message.message}\n"
            
            # Log to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            
            logger.info(f"[LOCAL] SMS logged: {message.phone_number}")
            
            return SMSResponse(
                success=True,
                message_id=f"local_mock_{datetime.utcnow().timestamp()}",
                provider="local"
            )
            
        except Exception as e:
            logger.error(f"Local SMS failed: {str(e)}")
            return SMSResponse(
                success=False,
                error_message=str(e),
                provider="local"
            )


class SMSTemplateEngine:
    """SMS template engine for common messages"""
    
    TEMPLATES = {
        "verification_code": "Your verification code is: {code}. Valid for 10 minutes. Don't share this code.",
        
        "welcome": "Welcome to Student Portal! Your account has been created successfully. Complete your profile to get started.",
        
        "profile_reminder": "Hi {name}! Your student profile is {percentage}% complete. Complete it now to access all features.",
        
        "password_reset": "Your password reset code is: {code}. Use this code to reset your password. Valid for 30 minutes.",
        
        "login_alert": "New login detected on your Student Portal account at {time}. If this wasn't you, please contact support.",
        
        "application_update": "Hi {name}! Your application status has been updated to: {status}. Check your portal for details.",
        
        "interview_reminder": "Reminder: You have an interview scheduled for {date} at {time}. Location: {location}",
        
        "document_submission": "Hi {name}! Please submit the following documents: {documents}. Deadline: {deadline}",
        
        "admission_result": "Congratulations {name}! Your admission status: {status}. Check your portal for complete details."
    }
    
    @classmethod
    def render_template(cls, template_name: str, context: Dict[str, Any]) -> str:
        """Render SMS template with context"""
        template = cls.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"SMS template '{template_name}' not found")
        
        try:
            return template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")


class SMSNotificationService:
    """SMS notification service with multiple providers"""
    
    def __init__(self):
        self.enabled = SMS_ENABLED
        self.current_provider_name = SMS_PROVIDER
        self.providers: Dict[str, BaseSMSProvider] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Initialize providers
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize SMS providers"""
        provider_classes = {
            SMSProvider.TWILIO.value: TwilioSMSProvider,
            SMSProvider.AWS_SNS.value: AWSSNSProvider,
            SMSProvider.NEXMO.value: NexmoSMSProvider,
            SMSProvider.LOCAL.value: LocalSMSProvider
        }
        
        for provider_name, config in SMS_CONFIGS.items():
            try:
                provider_class = provider_classes.get(provider_name)
                if provider_class:
                    provider = provider_class(config)
                    if provider.validate_config():
                        self.providers[provider_name] = provider
                        logger.info(f"SMS provider {provider_name} initialized successfully")
                    else:
                        logger.warning(f"SMS provider {provider_name} configuration invalid")
                else:
                    logger.warning(f"Unknown SMS provider: {provider_name}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize SMS provider {provider_name}: {str(e)}")
        
        # Fallback to local provider if none configured
        if not self.providers:
            logger.warning("No SMS providers configured, using local provider")
            self.providers["local"] = LocalSMSProvider({})
            self.current_provider_name = "local"
    
    async def send_sms(self, 
                      phone_number: str, 
                      message: str, 
                      provider_name: Optional[str] = None) -> SMSResponse:
        """Send SMS message"""
        try:
            if not self.enabled:
                logger.warning("SMS service is disabled")
                return SMSResponse(success=False, error_message="SMS service is disabled")
            
            provider_name = provider_name or self.current_provider_name
            provider = self.providers.get(provider_name)
            
            if not provider:
                logger.error(f"SMS provider {provider_name} not found")
                return SMSResponse(success=False, error_message=f"Provider {provider_name} not found")
            
            sms_message = SMSMessage(phone_number=phone_number, message=message)
            return await provider.send_sms(sms_message)
            
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return SMSResponse(success=False, error_message=str(e))
    
    async def send_template_sms(self, 
                               phone_number: str, 
                               template_name: str, 
                               context: Dict[str, Any],
                               provider_name: Optional[str] = None) -> SMSResponse:
        """Send templated SMS message"""
        try:
            message = SMSTemplateEngine.render_template(template_name, context)
            return await self.send_sms(phone_number, message, provider_name)
            
        except Exception as e:
            logger.error(f"Template SMS failed: {str(e)}")
            return SMSResponse(success=False, error_message=str(e))
    
    async def send_verification_code(self, phone_number: str, code: str) -> SMSResponse:
        """Send verification code SMS"""
        return await self.send_template_sms(
            phone_number=phone_number,
            template_name="verification_code",
            context={"code": code}
        )
    
    async def send_welcome_sms(self, phone_number: str) -> SMSResponse:
        """Send welcome SMS"""
        return await self.send_template_sms(
            phone_number=phone_number,
            template_name="welcome",
            context={}
        )
    
    async def send_profile_reminder(self, phone_number: str, name: str, percentage: int) -> SMSResponse:
        """Send profile completion reminder"""
        return await self.send_template_sms(
            phone_number=phone_number,
            template_name="profile_reminder",
            context={"name": name, "percentage": percentage}
        )
    
    async def send_password_reset_code(self, phone_number: str, code: str) -> SMSResponse:
        """Send password reset code"""
        return await self.send_template_sms(
            phone_number=phone_number,
            template_name="password_reset",
            context={"code": code}
        )
    
    def switch_provider(self, provider_name: str) -> bool:
        """Switch to different SMS provider"""
        if provider_name in self.providers:
            self.current_provider_name = provider_name
            logger.info(f"Switched to SMS provider: {provider_name}")
            return True
        else:
            logger.error(f"SMS provider {provider_name} not available")
            return False
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all SMS providers"""
        return {name: provider.validate_config() for name, provider in self.providers.items()}
    
    def get_available_templates(self) -> List[str]:
        """Get list of available SMS templates"""
        return list(SMSTemplateEngine.TEMPLATES.keys())


# Global instance
sms_service = SMSNotificationService()


def get_sms_service() -> SMSNotificationService:
    """Dependency to get SMS notification service"""
    return sms_service