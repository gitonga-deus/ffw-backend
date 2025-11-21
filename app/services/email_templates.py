"""
Email templates for the LMS platform.

This module contains HTML and plain text templates for all transactional emails.
Templates are designed to be responsive and accessible.
"""

from typing import Tuple


def get_base_template(title: str, content: str, header_color: str = "#4F46E5") -> str:
    """
    Get base HTML template with consistent styling.
    
    Args:
        title: Email title for header
        content: HTML content to insert
        header_color: Background color for header
        
    Returns:
        Complete HTML email template
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f3f4f6;
        }}
        .email-wrapper {{
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        .email-header {{
            background-color: {header_color};
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .email-header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .email-content {{
            padding: 40px 30px;
            background-color: #ffffff;
        }}
        .email-content h2 {{
            margin: 0 0 20px 0;
            font-size: 24px;
            font-weight: 600;
            color: #111827;
        }}
        .email-content p {{
            margin: 0 0 16px 0;
            font-size: 16px;
            color: #4b5563;
        }}
        .button {{
            display: inline-block;
            padding: 14px 32px;
            background-color: {header_color};
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            margin: 20px 0;
            transition: background-color 0.2s;
        }}
        .button:hover {{
            opacity: 0.9;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .link-text {{
            word-break: break-all;
            color: {header_color};
            font-size: 14px;
            padding: 10px;
            background-color: #f9fafb;
            border-radius: 4px;
            display: inline-block;
            margin: 10px 0;
        }}
        .info-box {{
            background-color: #f9fafb;
            border-left: 4px solid {header_color};
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .certificate-box {{
            background-color: #ffffff;
            border: 2px solid {header_color};
            border-radius: 8px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }}
        .certificate-box h3 {{
            margin: 0 0 15px 0;
            color: {header_color};
            font-size: 22px;
        }}
        .certificate-id {{
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #111827;
            background-color: #f3f4f6;
            padding: 10px 20px;
            border-radius: 4px;
            display: inline-block;
            margin: 10px 0;
        }}
        .email-footer {{
            background-color: #f9fafb;
            padding: 30px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            border-top: 1px solid #e5e7eb;
        }}
        .email-footer p {{
            margin: 5px 0;
            color: #6b7280;
        }}
        .divider {{
            height: 1px;
            background-color: #e5e7eb;
            margin: 30px 0;
        }}
        @media only screen and (max-width: 600px) {{
            .email-content {{
                padding: 30px 20px;
            }}
            .email-header h1 {{
                font-size: 24px;
            }}
            .button {{
                display: block;
                width: 100%;
                box-sizing: border-box;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            <div class="email-header">
                <h1>{title}</h1>
            </div>
            <div class="email-content">
                {content}
            </div>
            <div class="email-footer">
                <p><strong>LMS Platform</strong></p>
                <p>&copy; 2024 LMS Platform. All rights reserved.</p>
                <p style="margin-top: 15px; font-size: 12px;">
                    This is an automated message, please do not reply to this email.
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""


def get_verification_email_template(full_name: str, verification_url: str) -> Tuple[str, str]:
    """
    Get email verification template.
    
    Args:
        full_name: User's full name
        verification_url: URL for email verification
        
    Returns:
        Tuple of (html_content, text_content)
    """
    content = f"""
        <h2>Hi {full_name},</h2>
        <p>Thank you for registering with LMS Platform! We're excited to have you join our learning community.</p>
        <p>To complete your registration and activate your account, please verify your email address by clicking the button below:</p>
        
        <div class="button-container">
            <a href="{verification_url}" class="button">Verify Email Address</a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <div class="link-text">{verification_url}</div>
        
        <div class="info-box">
            <p style="margin: 0;"><strong>⏰ Important:</strong> This verification link will expire in 24 hours.</p>
        </div>
        
        <p>If you didn't create an account with LMS Platform, you can safely ignore this email.</p>
    """
    
    html = get_base_template("Welcome to LMS Platform!", content, "#4F46E5")
    
    text = f"""
Welcome to LMS Platform!

Hi {full_name},

Thank you for registering with LMS Platform! We're excited to have you join our learning community.

To complete your registration and activate your account, please verify your email address by visiting:

{verification_url}

This verification link will expire in 24 hours.

If you didn't create an account with LMS Platform, you can safely ignore this email.

---
LMS Platform
© 2024 LMS Platform. All rights reserved.
"""
    
    return html, text


def get_password_reset_email_template(full_name: str, reset_url: str) -> Tuple[str, str]:
    """
    Get password reset template.
    
    Args:
        full_name: User's full name
        reset_url: URL for password reset
        
    Returns:
        Tuple of (html_content, text_content)
    """
    content = f"""
        <h2>Hi {full_name},</h2>
        <p>We received a request to reset the password for your LMS Platform account.</p>
        <p>Click the button below to create a new password:</p>
        
        <div class="button-container">
            <a href="{reset_url}" class="button">Reset Password</a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <div class="link-text">{reset_url}</div>
        
        <div class="info-box">
            <p style="margin: 0;"><strong>⏰ Important:</strong> This password reset link will expire in 1 hour.</p>
        </div>
        
        <p>If you didn't request a password reset, please ignore this email or contact our support team if you have concerns about your account security.</p>
        
        <p style="margin-top: 30px; font-size: 14px; color: #6b7280;">
            For security reasons, we never ask for your password via email. If you receive suspicious emails claiming to be from LMS Platform, please report them to our support team.
        </p>
    """
    
    html = get_base_template("Password Reset Request", content, "#4F46E5")
    
    text = f"""
Password Reset Request

Hi {full_name},

We received a request to reset the password for your LMS Platform account.

To create a new password, visit this link:

{reset_url}

This password reset link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact our support team if you have concerns about your account security.

For security reasons, we never ask for your password via email.

---
LMS Platform
© 2024 LMS Platform. All rights reserved.
"""
    
    return html, text


def get_welcome_email_template(full_name: str, dashboard_url: str) -> Tuple[str, str]:
    """
    Get welcome email template for enrolled students.
    
    Args:
        full_name: User's full name
        dashboard_url: URL to student dashboard
        
    Returns:
        Tuple of (html_content, text_content)
    """
    content = f"""
        <h2>Congratulations, {full_name}! 🎉</h2>
        <p>Your enrollment has been successfully confirmed! Welcome to our learning community.</p>
        
        <div class="info-box">
            <p style="margin: 0;"><strong>✅ You now have full access to:</strong></p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                <li>All course modules and content</li>
                <li>Video lectures and downloadable resources</li>
                <li>Interactive exercises and assessments</li>
                <li>Progress tracking and certificates</li>
            </ul>
        </div>
        
        <p>Ready to start your learning journey? Access your dashboard to begin:</p>
        
        <div class="button-container">
            <a href="{dashboard_url}" class="button">Go to Dashboard</a>
        </div>
        
        <div class="divider"></div>
        
        <p><strong>Tips for Success:</strong></p>
        <ul style="color: #4b5563; margin: 10px 0; padding-left: 20px;">
            <li>Set aside dedicated time for learning each day</li>
            <li>Complete modules in order for the best experience</li>
            <li>Don't hesitate to revisit content as needed</li>
            <li>Track your progress and celebrate milestones</li>
        </ul>
        
        <p style="margin-top: 30px;">We're excited to support you on this journey. Let's get started!</p>
    """
    
    html = get_base_template("Welcome to the Course!", content, "#10B981")
    
    text = f"""
Welcome to the Course!

Congratulations, {full_name}! 🎉

Your enrollment has been successfully confirmed! Welcome to our learning community.

You now have full access to:
- All course modules and content
- Video lectures and downloadable resources
- Interactive exercises and assessments
- Progress tracking and certificates

Ready to start your learning journey? Access your dashboard:

{dashboard_url}

Tips for Success:
- Set aside dedicated time for learning each day
- Complete modules in order for the best experience
- Don't hesitate to revisit content as needed
- Track your progress and celebrate milestones

We're excited to support you on this journey. Let's get started!

---
LMS Platform
© 2024 LMS Platform. All rights reserved.
"""
    
    return html, text


def get_course_completion_email_template(
    full_name: str,
    certificate_url: str,
    cert_id: str,
    verify_url: str,
    certificate_page_url: str
) -> Tuple[str, str]:
    """
    Get course completion email template with certificate.
    
    Args:
        full_name: User's full name
        certificate_url: URL to download certificate
        cert_id: Certificate ID
        verify_url: URL to verify certificate
        certificate_page_url: URL to certificate page
        
    Returns:
        Tuple of (html_content, text_content)
    """
    content = f"""
        <h2>🎉 Congratulations, {full_name}!</h2>
        <p>You've done it! You have successfully completed the course, and we couldn't be more proud of your dedication and hard work throughout this learning journey.</p>
        
        <div class="certificate-box">
            <h3>🏆 Your Certificate is Ready!</h3>
            <p style="margin: 15px 0;">Certificate ID:</p>
            <div class="certificate-id">{cert_id}</div>
            
            <div class="button-container">
                <a href="{certificate_url}" class="button">Download Certificate</a>
            </div>
        </div>
        
        <p><strong>Verify Your Certificate:</strong></p>
        <p>Anyone can verify the authenticity of your certificate using this link:</p>
        <div class="link-text">{verify_url}</div>
        
        <div class="divider"></div>
        
        <p><strong>What's Next?</strong></p>
        <ul style="color: #4b5563; margin: 10px 0; padding-left: 20px;">
            <li>Download and share your certificate on LinkedIn and other professional networks</li>
            <li>Add your new skills to your resume and portfolio</li>
            <li>Apply what you've learned in real-world projects</li>
            <li>Consider leaving a review to help future students</li>
        </ul>
        
        <div class="button-container">
            <a href="{certificate_page_url}" class="button">View Certificate Page</a>
        </div>
        
        <p style="margin-top: 30px;">Thank you for being part of our learning community. We wish you continued success in your journey!</p>
    """
    
    html = get_base_template("🎉 Course Completed!", content, "#8B5CF6")
    
    text = f"""
🎉 Course Completed!

Congratulations, {full_name}!

You've done it! You have successfully completed the course, and we couldn't be more proud of your dedication and hard work throughout this learning journey.

🏆 Your Certificate is Ready!

Certificate ID: {cert_id}

Download your certificate:
{certificate_url}

Verify Your Certificate:
Anyone can verify the authenticity of your certificate using this link:
{verify_url}

What's Next?
- Download and share your certificate on LinkedIn and other professional networks
- Add your new skills to your resume and portfolio
- Apply what you've learned in real-world projects
- Consider leaving a review to help future students

View your certificate page:
{certificate_page_url}

Thank you for being part of our learning community. We wish you continued success in your journey!

---
LMS Platform
© 2024 LMS Platform. All rights reserved.
"""
    
    return html, text


def get_notification_email_template(
    full_name: str,
    title: str,
    message: str,
    dashboard_url: str
) -> Tuple[str, str]:
    """
    Get notification email template.
    
    Args:
        full_name: User's full name
        title: Notification title
        message: Notification message
        dashboard_url: URL to dashboard
        
    Returns:
        Tuple of (html_content, text_content)
    """
    content = f"""
        <h2>Hi {full_name},</h2>
        <p>You have a new notification from LMS Platform:</p>
        
        <div class="info-box">
            <p style="margin: 0; white-space: pre-wrap; font-size: 16px; line-height: 1.6;">{message}</p>
        </div>
        
        <p>Visit your dashboard to stay updated with the latest course information and announcements:</p>
        
        <div class="button-container">
            <a href="{dashboard_url}" class="button">Go to Dashboard</a>
        </div>
    """
    
    html = get_base_template(f"📢 {title}", content, "#4F46E5")
    
    text = f"""
📢 {title}

Hi {full_name},

You have a new notification from LMS Platform:

{message}

Visit your dashboard to stay updated:
{dashboard_url}

---
LMS Platform
© 2024 LMS Platform. All rights reserved.
"""
    
    return html, text
