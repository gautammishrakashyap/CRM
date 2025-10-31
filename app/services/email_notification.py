import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from jinja2 import Template
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.core.config import (
    SMTP_CONFIGS, DEFAULT_SMTP_PROVIDER, EMAIL_ENABLED,
    EMAIL_TEMPLATES_DIR, FROM_EMAIL, FROM_NAME
)

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    """Email attachment data"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Email message data"""
    to_emails: List[str]
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    attachments: List[EmailAttachment] = None
    cc_emails: List[str] = None
    bcc_emails: List[str] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.cc_emails is None:
            self.cc_emails = []
        if self.bcc_emails is None:
            self.bcc_emails = []


class SMTPProvider:
    """SMTP provider configuration and connection"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.host = config.get("host")
        self.port = config.get("port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.use_tls = config.get("use_tls", True)
        self.use_ssl = config.get("use_ssl", False)
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
    
    def create_connection(self) -> smtplib.SMTP:
        """Create SMTP connection"""
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            logger.info(f"SMTP connection established with {self.name}")
            return server
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {str(e)}")
            raise


class EmailTemplateEngine:
    """Email template rendering engine"""
    
    def __init__(self, templates_dir: str = EMAIL_TEMPLATES_DIR):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self._ensure_default_templates()
    
    def _ensure_default_templates(self):
        """Create default email templates if they don't exist"""
        templates = {
            "welcome.html": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to Student Portal</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f8f9fa; }
                    .button { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                    .footer { text-align: center; padding: 20px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to Student Portal!</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ student_name }}!</h2>
                        <p>Welcome to our Student Portal. Your account has been successfully created.</p>
                        <p>Your User ID: <strong>{{ user_id }}</strong></p>
                        <p>Please complete your profile to access all features:</p>
                        <p style="text-align: center;">
                            <a href="{{ profile_url }}" class="button">Complete Profile</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© 2024 Student Portal. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            "profile_completion_reminder.html": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Complete Your Profile</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #28a745; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f8f9fa; }
                    .progress { background: #e9ecef; height: 20px; border-radius: 10px; margin: 20px 0; }
                    .progress-bar { background: #28a745; height: 100%; border-radius: 10px; }
                    .button { display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Complete Your Profile</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ student_name }}!</h2>
                        <p>Your profile is {{ completion_percentage }}% complete.</p>
                        <div class="progress">
                            <div class="progress-bar" style="width: {{ completion_percentage }}%;"></div>
                        </div>
                        <p>Missing sections:</p>
                        <ul>
                            {% for missing in missing_sections %}
                            <li>{{ missing }}</li>
                            {% endfor %}
                        </ul>
                        <p style="text-align: center;">
                            <a href="{{ profile_url }}" class="button">Complete Profile</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            "email_verification.html": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Verify Your Email</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #6f42c1; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f8f9fa; }
                    .button { display: inline-block; padding: 10px 20px; background: #6f42c1; color: white; text-decoration: none; border-radius: 5px; }
                    .code { font-size: 24px; font-weight: bold; text-align: center; padding: 20px; background: white; border: 2px dashed #6f42c1; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Verify Your Email</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ student_name }}!</h2>
                        <p>Please verify your email address to complete your registration.</p>
                        <div class="code">{{ verification_code }}</div>
                        <p>Or click the button below:</p>
                        <p style="text-align: center;">
                            <a href="{{ verification_url }}" class="button">Verify Email</a>
                        </p>
                        <p><small>This verification code will expire in 24 hours.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            
            "password_reset.html": """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Reset Your Password</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f8f9fa; }
                    .button { display: inline-block; padding: 10px 20px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Reset Your Password</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {{ student_name }}!</h2>
                        <p>You requested a password reset for your account.</p>
                        <p>Click the button below to reset your password:</p>
                        <p style="text-align: center;">
                            <a href="{{ reset_url }}" class="button">Reset Password</a>
                        </p>
                        <p><small>This link will expire in 1 hour. If you didn't request this, please ignore this email.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        for template_name, content in templates.items():
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                template_path.write_text(content.strip())
                logger.info(f"Created email template: {template_name}")
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render email template with context"""
        try:
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"Template {template_name} not found")
            
            template_content = template_path.read_text()
            template = Template(template_content)
            return template.render(**context)
            
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise


class EmailNotificationService:
    """Email notification service with multiple SMTP providers"""
    
    def __init__(self):
        self.enabled = EMAIL_ENABLED
        self.providers = {}
        self.default_provider = DEFAULT_SMTP_PROVIDER
        self.template_engine = EmailTemplateEngine()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Initialize SMTP providers
        for provider_name, config in SMTP_CONFIGS.items():
            try:
                self.providers[provider_name] = SMTPProvider(provider_name, config)
                logger.info(f"SMTP provider {provider_name} configured")
            except Exception as e:
                logger.error(f"Failed to configure SMTP provider {provider_name}: {str(e)}")
        
        if not self.providers:
            logger.warning("No SMTP providers configured successfully")
            self.enabled = False
    
    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message from EmailMessage"""
        msg = MIMEMultipart('alternative')
        
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = ", ".join(message.to_emails)
        msg['Subject'] = message.subject
        
        if message.cc_emails:
            msg['Cc'] = ", ".join(message.cc_emails)
        
        # Add text content
        if message.text_content:
            text_part = MIMEText(message.text_content, 'plain')
            msg.attach(text_part)
        
        # Add HTML content
        if message.html_content:
            html_part = MIMEText(message.html_content, 'html')
            msg.attach(html_part)
        
        # Add attachments
        for attachment in message.attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.filename}'
            )
            msg.attach(part)
        
        return msg
    
    def _send_email_sync(self, message: EmailMessage, provider_name: str = None) -> bool:
        """Send email synchronously"""
        try:
            if not self.enabled:
                logger.warning("Email service is disabled")
                return False
            
            provider_name = provider_name or self.default_provider
            provider = self.providers.get(provider_name)
            
            if not provider:
                logger.error(f"SMTP provider {provider_name} not found")
                return False
            
            # Create MIME message
            mime_msg = self._create_mime_message(message)
            
            # Get all recipients
            all_recipients = message.to_emails + message.cc_emails + message.bcc_emails
            
            # Send email
            with provider.create_connection() as server:
                server.send_message(mime_msg, to_addrs=all_recipients)
            
            logger.info(f"Email sent successfully via {provider_name} to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via {provider_name}: {str(e)}")
            return False
    
    async def send_email(self, message: EmailMessage, provider_name: str = None) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._send_email_sync, 
            message, 
            provider_name
        )
    
    async def send_template_email(self, 
                                template_name: str, 
                                to_emails: List[str], 
                                subject: str, 
                                context: Dict[str, Any],
                                provider_name: str = None) -> bool:
        """Send templated email"""
        try:
            # Render template
            html_content = self.template_engine.render_template(template_name, context)
            
            # Create message
            message = EmailMessage(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content
            )
            
            return await self.send_email(message, provider_name)
            
        except Exception as e:
            logger.error(f"Failed to send template email {template_name}: {str(e)}")
            return False
    
    async def send_welcome_email(self, user_email: str, student_name: str, user_id: str) -> bool:
        """Send welcome email to new student"""
        context = {
            "student_name": student_name,
            "user_id": user_id,
            "profile_url": f"{FROM_EMAIL}/profile/complete"  # You can configure this URL
        }
        
        return await self.send_template_email(
            template_name="welcome.html",
            to_emails=[user_email],
            subject="Welcome to Student Portal!",
            context=context
        )
    
    async def send_profile_completion_reminder(self, 
                                             user_email: str, 
                                             student_name: str, 
                                             completion_percentage: int,
                                             missing_sections: List[str]) -> bool:
        """Send profile completion reminder"""
        context = {
            "student_name": student_name,
            "completion_percentage": completion_percentage,
            "missing_sections": missing_sections,
            "profile_url": f"{FROM_EMAIL}/profile/complete"
        }
        
        return await self.send_template_email(
            template_name="profile_completion_reminder.html",
            to_emails=[user_email],
            subject="Complete Your Student Profile",
            context=context
        )
    
    async def send_email_verification(self, 
                                    user_email: str, 
                                    student_name: str, 
                                    verification_code: str,
                                    verification_url: str) -> bool:
        """Send email verification"""
        context = {
            "student_name": student_name,
            "verification_code": verification_code,
            "verification_url": verification_url
        }
        
        return await self.send_template_email(
            template_name="email_verification.html",
            to_emails=[user_email],
            subject="Verify Your Email Address",
            context=context
        )
    
    async def send_password_reset(self, 
                                user_email: str, 
                                student_name: str, 
                                reset_url: str) -> bool:
        """Send password reset email"""
        context = {
            "student_name": student_name,
            "reset_url": reset_url
        }
        
        return await self.send_template_email(
            template_name="password_reset.html",
            to_emails=[user_email],
            subject="Reset Your Password",
            context=context
        )
    
    def test_provider(self, provider_name: str) -> bool:
        """Test SMTP provider connection"""
        try:
            provider = self.providers.get(provider_name)
            if not provider:
                return False
            
            with provider.create_connection() as server:
                server.noop()  # Send a NOOP command to test connection
            
            logger.info(f"SMTP provider {provider_name} test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP provider {provider_name} test failed: {str(e)}")
            return False
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all SMTP providers"""
        status = {}
        for provider_name in self.providers.keys():
            status[provider_name] = self.test_provider(provider_name)
        return status


# Global instance
email_service = EmailNotificationService()


def get_email_service() -> EmailNotificationService:
    """Dependency to get email notification service"""
    return email_service