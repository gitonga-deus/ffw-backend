"""
Email service for sending transactional emails via Resend.

This service handles all email communications including:
- Email verification
- Password reset
- Welcome emails
- Course completion notifications
- Admin notifications
"""

import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.services.email_templates import (
    get_verification_email_template,
    get_password_reset_email_template,
    get_welcome_email_template,
    get_course_completion_email_template,
    get_signature_confirmation_email_template,
    get_notification_email_template
)


class EmailService:
    """Service for sending emails via Resend API."""
    
    def __init__(self):
        self.api_key = settings.resend_api_key
        self.base_url = "https://api.resend.com"
        self.from_email = settings.email_from
        self.timeout = 30.0
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email using Resend API.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            html: HTML content of the email
            text: Plain text version of the email (optional)
            reply_to: Reply-to email address (optional)
            
        Returns:
            Dict containing success status and message/error details
        """
        if not self.api_key:
            # Development mode - log email instead of sending
            print(f"\n{'='*60}")
            print(f"[DEV MODE] Email would be sent:")
            print(f"To: {to}")
            print(f"Subject: {subject}")
            print(f"{'='*60}\n")
            return {"success": True, "message": "Email logged (dev mode)", "id": "dev-mode"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "from": self.from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
                
                if text:
                    payload["text"] = text
                    
                if reply_to:
                    payload["reply_to"] = reply_to
                
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "id": data.get("id")
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error occurred: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg = f"{error_msg} - {error_detail.get('message', error_detail)}"
            except:
                error_msg = f"{error_msg} - {e.response.text}"
            print(f"Failed to send email to {to}: {error_msg}")
            return {"success": False, "error": error_msg}
            
        except httpx.TimeoutException:
            error_msg = "Request timed out"
            print(f"Failed to send email to {to}: {error_msg}")
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"Failed to send email to {to}: {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def send_verification_email(
        self,
        to: str,
        full_name: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Send email verification email to new user.
        
        Args:
            to: User's email address
            full_name: User's full name
            token: Verification token
            
        Returns:
            Dict containing success status and details
        """
        verification_url = f"{settings.frontend_url}/verify-email?token={token}"
        
        html, text = get_verification_email_template(
            full_name=full_name,
            verification_url=verification_url
        )
        
        return await self.send_email(
            to=to,
            subject="Verify Your Email Address",
            html=html,
            text=text
        )
    
    async def send_password_reset_email(
        self,
        to: str,
        full_name: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Send password reset email to user.
        
        Args:
            to: User's email address
            full_name: User's full name
            token: Password reset token
            
        Returns:
            Dict containing success status and details
        """
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        
        html, text = get_password_reset_email_template(
            full_name=full_name,
            reset_url=reset_url
        )
        
        return await self.send_email(
            to=to,
            subject="Reset Your Password",
            html=html,
            text=text
        )
    
    async def send_welcome_email(
        self,
        to: str,
        full_name: str
    ) -> Dict[str, Any]:
        """
        Send welcome email after successful enrollment.
        
        Args:
            to: User's email address
            full_name: User's full name
            
        Returns:
            Dict containing success status and details
        """
        dashboard_url = f"{settings.frontend_url}/dashboard"
        
        html, text = get_welcome_email_template(
            full_name=full_name,
            dashboard_url=dashboard_url
        )
        
        return await self.send_email(
            to=to,
            subject="Welcome to the Course!",
            html=html,
            text=text
        )
    
    async def send_course_completion_email(
        self,
        to: str,
        full_name: str,
        certificate_url: str,
        cert_id: str
    ) -> Dict[str, Any]:
        """
        Send course completion email with certificate link.
        
        Args:
            to: User's email address
            full_name: User's full name
            certificate_url: URL to download certificate
            cert_id: Certificate ID for verification
            
        Returns:
            Dict containing success status and details
        """
        verify_url = f"{settings.frontend_url}/verify-certificate/{cert_id}"
        certificate_page_url = f"{settings.frontend_url}/certificate"
        
        html, text = get_course_completion_email_template(
            full_name=full_name,
            certificate_url=certificate_url,
            cert_id=cert_id,
            verify_url=verify_url,
            certificate_page_url=certificate_page_url
        )
        
        return await self.send_email(
            to=to,
            subject="🎉 Course Completed - Your Certificate is Ready!",
            html=html,
            text=text
        )
    
    async def send_signature_confirmation_email(
        self,
        to: str,
        full_name: str
    ) -> Dict[str, Any]:
        """
        Send signature confirmation email after student submits signature.
        
        Args:
            to: User's email address
            full_name: User's full name
            
        Returns:
            Dict containing success status and details
        """
        course_url = f"{settings.frontend_url}/students/course"
        
        html, text = get_signature_confirmation_email_template(
            full_name=full_name,
            course_url=course_url
        )
        
        return await self.send_email(
            to=to,
            subject="✅ Signature Confirmed - Ready to Learn!",
            html=html,
            text=text
        )
    
    async def send_notification_email(
        self,
        to: str,
        full_name: str,
        title: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send notification email to user.
        
        Args:
            to: User's email address
            full_name: User's full name
            title: Notification title
            message: Notification message content
            
        Returns:
            Dict containing success status and details
        """
        dashboard_url = f"{settings.frontend_url}/dashboard"
        
        html, text = get_notification_email_template(
            full_name=full_name,
            title=title,
            message=message,
            dashboard_url=dashboard_url
        )
        
        return await self.send_email(
            to=to,
            subject=title,
            html=html,
            text=text
        )


# Singleton instance
email_service = EmailService()
