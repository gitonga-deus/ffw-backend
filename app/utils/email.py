"""
DEPRECATED: This module is deprecated and kept for backward compatibility only.

Please use the new email service instead:
    from app.services.email_service import email_service

The new service provides:
- Better error handling
- Improved template system
- Comprehensive documentation
- Better testing support

See: backend/app/services/EMAIL_SERVICE_SETUP.md for migration guide
"""

import httpx
from typing import Optional
from app.config import settings


class EmailService:
    """
    DEPRECATED: Use app.services.email_service instead.
    
    Service for sending emails via Resend.
    """
    
    def __init__(self):
        self.api_key = settings.resend_api_key
        self.base_url = "https://api.resend.com"
        self.from_email = "Financially Fit World <noreply@yourdomain.com>"
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """Send an email using Resend API."""
        if not self.api_key:
            print(f"Email would be sent to {to}: {subject}")
            print(f"Content: {text or html}")
            return True  # Skip in development if no API key
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text
                    }
                )
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Failed to send email: {str(e)}")
                return False
    
    async def send_verification_email(self, to: str, full_name: str, token: str) -> bool:
        """Send email verification email."""
        verification_url = f"{settings.frontend_url}/verify-email?token={token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #4F46E5; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Financially Fit World!</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>Thank you for registering with Financially Fit World. To complete your registration, 
                    please verify your email address by clicking the button below:</p>
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Financially Fit World. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Welcome to Financially Fit World!
        
        Hi {full_name},
        
        Thank you for registering. Please verify your email address by visiting:
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        return await self.send_email(to, "Verify Your Email Address", html, text)
    
    async def send_password_reset_email(self, to: str, full_name: str, token: str) -> bool:
        """Send password reset email."""
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #4F46E5; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4F46E5;">{reset_url}</p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, please ignore this email or contact support 
                    if you have concerns.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Financially Fit World. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Password Reset Request
        
        Hi {full_name},
        
        We received a request to reset your password. Visit this link to create a new password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        """
        
        return await self.send_email(to, "Reset Your Password", html, text)
    
    async def send_welcome_email(self, to: str, full_name: str) -> bool:
        """Send welcome email after successful enrollment."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #10B981; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to the Course!</h1>
                </div>
                <div class="content">
                    <h2>Congratulations {full_name}!</h2>
                    <p>Your enrollment has been confirmed. You now have full access to all course materials.</p>
                    <p>Get started with your learning journey:</p>
                    <div style="text-align: center;">
                        <a href="{settings.frontend_url}/dashboard" class="button">Go to Dashboard</a>
                    </div>
                    <p>We're excited to have you on board!</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Financially Fit World. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to, "Welcome to the Course!", html)
    
    async def send_course_completion_email(
        self,
        to: str,
        full_name: str,
        certificate_url: str,
        cert_id: str
    ) -> bool:
        """Send course completion email with certificate link."""
        verify_url = f"{settings.frontend_url}/verify-certificate/{cert_id}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #8B5CF6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #8B5CF6; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .certificate-box {{ background-color: white; border: 2px solid #8B5CF6; 
                                   border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Congratulations!</h1>
                </div>
                <div class="content">
                    <h2>Well Done, {full_name}!</h2>
                    <p>You have successfully completed the course! We're incredibly proud of your dedication 
                    and hard work throughout this learning journey.</p>
                    
                    <div class="certificate-box">
                        <h3>Your Certificate is Ready!</h3>
                        <p>Certificate ID: <strong>{cert_id}</strong></p>
                        <div style="text-align: center;">
                            <a href="{certificate_url}" class="button">Download Certificate</a>
                        </div>
                    </div>
                    
                    <p>You can verify your certificate at any time using this link:</p>
                    <p style="word-break: break-all; color: #8B5CF6;">{verify_url}</p>
                    
                    <p>Share your achievement with your network and showcase your new skills!</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{settings.frontend_url}/certificate" class="button">View Certificate</a>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Financially Fit World. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Congratulations!
        
        Well Done, {full_name}!
        
        You have successfully completed the course!
        
        Your Certificate is Ready!
        Certificate ID: {cert_id}
        
        Download your certificate: {certificate_url}
        Verify your certificate: {verify_url}
        
        Share your achievement with your network!
        """
        
        return await self.send_email(to, "🎉 Course Completed - Your Certificate is Ready!", html, text)
    
    async def send_notification_email(
        self,
        to: str,
        full_name: str,
        title: str,
        message: str
    ) -> bool:
        """Send notification email to user."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9fafb; }}
                .message-box {{ background-color: white; border-left: 4px solid #4F46E5; 
                               padding: 20px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #4F46E5; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📢 {title}</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <div class="message-box">
                        <p style="white-space: pre-wrap;">{message}</p>
                    </div>
                    <div style="text-align: center;">
                        <a href="{settings.frontend_url}/dashboard" class="button">Go to Dashboard</a>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Financially Fit World. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        {title}
        
        Hi {full_name},
        
        {message}
        
        Visit your dashboard: {settings.frontend_url}/dashboard
        """
        
        return await self.send_email(to, title, html, text)


# Singleton instance
email_service = EmailService()
