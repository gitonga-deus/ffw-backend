"""
Email templates for the Financially Fit World platform.

This module contains HTML and plain text templates for all transactional emails.
Templates are designed to be responsive and accessible.
"""

from typing import Tuple


def get_base_template(title: str, content: str, header_color: str = "#049ad1") -> str:
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
        .email-header img {{
            max-width: 150px;
            height: auto;
            margin: 0 auto 15px;
            display: block;
        }}
        .email-header h1 {{
            margin: 0 0 5px 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .email-header h2 {{
            margin: 0;
            font-size: 18px;
            font-weight: 400;
            opacity: 0.95;
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
                <img src="https://ffw-frontend-ten.vercel.app/logo/logo.png" alt="Financially Fit World Logo" />
                <h1>Financially Fit World</h1>
                <h2>{title}</h2>
            </div>
            <div class="email-content">
                {content}
            </div>
            <div class="email-footer">
                <p><strong>FiNFIT World</strong></p>
                <p>&copy; 2024 FiNFIT World. All rights reserved.</p>
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
        <p>You're just one step away from unlocking your personalized fitness and finance experience.</p>
        <p>To complete your registration and activate your account, please verify your email by clicking the link below:</p>
        
        <div class="button-container">
            <a href="{verification_url}" class="button">Verify My Account</a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <div class="link-text">{verification_url}</div>
        
        <p>If you did not create an account with FiNFIT World, please ignore this message.</p>
        
        <p style="margin-top: 30px;">Thank you for joining our community — we are excited to support your journey towards a stronger future!</p>
        
        <p><strong>Stay fit, stay smart,</strong><br>The FiNFIT World Team</p>
    """
    
    html = get_base_template("Verify Your Email", content, "#049ad1")
    
    text = f"""
Verify Your Email

Hi {full_name},

You're just one step away from unlocking your personalized fitness and finance experience.

To complete your registration and activate your account, please verify your email by clicking the link below:

{verification_url}

If you did not create an account with FiNFIT World, please ignore this message.

Thank you for joining our community — we are excited to support your journey towards a stronger future!

Stay fit, stay smart,
The FiNFIT World Team

---
FiNFIT World
© 2024 FiNFIT World. All rights reserved.
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
        <p>We received a request to reset the password for your FiNFIT World account.</p>
        <p>Click the button below to create a new password:</p>
        
        <div class="button-container">
            <a href="{reset_url}" class="button">Reset Password</a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <div class="link-text">{reset_url}</div>
        
        <p>If you did not make this request with your FiNFIT World account, please ignore this message.</p>
        
        <p style="margin-top: 30px;">Thank you for joining our community — we are excited to support your journey towards a stronger future!</p>
        
        <p><strong>Stay fit, stay smart,</strong><br>The FiNFIT World Team</p>
    """
    
    html = get_base_template("Password Reset Request", content, "#049ad1")
    
    text = f"""
Password Reset Request

Hi {full_name},

We received a request to reset the password for your FiNFIT World account.

Click the button below to create a new password:

{reset_url}

If you did not make this request with your FiNFIT World account, please ignore this message.

Thank you for joining our community — we are excited to support your journey towards a stronger future!

Stay fit, stay smart,
The FiNFIT World Team

---
FiNFIT World
© 2024 FiNFIT World. All rights reserved.
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
        <h2>Welcome to FiNFIT World</h2>
        <p>We are excited to have you join a community built to help you grow, thrive, and achieve more in your financial journey.</p>
        
        <p>Your account is now active, and you are all set to explore everything FiNFIT World has to offer — learning resources and tailored features designed to elevate your financial independence.</p>
        
        <p><strong>Here's what you can do next:</strong></p>
        <ul style="color: #4b5563; margin: 10px 0; padding-left: 20px;">
            <li>✔ Log in to your dashboard</li>
            <li>✔ Set up your profile</li>
            <li>✔ Explore tools and resources made just for you</li>
        </ul>
        
        <div class="button-container">
            <a href="{dashboard_url}" class="button">Go to Dashboard</a>
        </div>
        
        <p style="margin-top: 30px;">Thank you for being part of FiNFIT World — we are excited to have you on board!</p>
        
        <p><strong>Best regards,</strong><br>The FiNFIT World Team</p>
    """
    
    html = get_base_template("Welcome to FiNFIT World", content, "#049ad1")
    
    text = f"""
Welcome to FiNFIT World

We are excited to have you join a community built to help you grow, thrive, and achieve more in your financial journey.

Your account is now active, and you are all set to explore everything FiNFIT World has to offer — learning resources and tailored features designed to elevate your financial independence.

Here's what you can do next:
• ✔ Log in to your dashboard
• ✔ Set up your profile
• ✔ Explore tools and resources made just for you

Access your dashboard:
{dashboard_url}

Thank you for being part of FiNFIT World — we are excited to have you on board!

Best regards,
The FiNFIT World Team

---
FiNFIT World
© 2024 FiNFIT World. All rights reserved.
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
    
    html = get_base_template("🎉 Course Completed!", content, "#049ad1")
    
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
Financially Fit World
© 2024 Financially Fit World. All rights reserved.
"""
    
    return html, text


def get_signature_confirmation_email_template(
    full_name: str,
    course_url: str
) -> Tuple[str, str]:
    """
    Get signature confirmation email template.
    
    Args:
        full_name: User's full name
        course_url: URL to course page
        
    Returns:
        Tuple of (html_content, text_content)
    """
    content = f"""
        <h2>Great job, {full_name}! ✅</h2>
        <p>Your digital signature has been successfully submitted and recorded.</p>
        
        <div class="info-box">
            <p style="margin: 0;"><strong>✅ Enrollment Complete!</strong></p>
            <p style="margin: 10px 0 0 0;">You're all set to begin your learning journey. Your signature confirms your commitment to completing the course.</p>
        </div>
        
        <p><strong>What's Next?</strong></p>
        <ul style="color: #4b5563; margin: 10px 0; padding-left: 20px;">
            <li>Access all course modules and content</li>
            <li>Watch video lectures at your own pace</li>
            <li>Complete exercises and track your progress</li>
            <li>Earn your certificate upon completion</li>
        </ul>
        
        <p>Ready to start learning? Click the button below to access your course:</p>
        
        <div class="button-container">
            <a href="{course_url}" class="button">Start Learning</a>
        </div>
        
        <div class="divider"></div>
        
        <p style="font-size: 14px; color: #6b7280;">
            <strong>Pro Tip:</strong> Set aside dedicated time each day for learning. Consistency is key to successfully completing the course and achieving your goals.
        </p>
        
        <p style="margin-top: 30px;">We're excited to support you on this learning journey. Let's get started!</p>
    """
    
    html = get_base_template("Signature Confirmed - Ready to Learn!", content, "#049ad1")
    
    text = f"""
Signature Confirmed - Ready to Learn!

Great job, {full_name}! ✅

Your digital signature has been successfully submitted and recorded.

✅ Enrollment Complete!
You're all set to begin your learning journey. Your signature confirms your commitment to completing the course.

What's Next?
- Access all course modules and content
- Watch video lectures at your own pace
- Complete exercises and track your progress
- Earn your certificate upon completion

Ready to start learning? Access your course:
{course_url}

Pro Tip: Set aside dedicated time each day for learning. Consistency is key to successfully completing the course and achieving your goals.

We're excited to support you on this learning journey. Let's get started!

---
Financially Fit World
© 2024 Financially Fit World. All rights reserved.
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
        <p>You have a new notification from Financially Fit World:</p>
        
        <div class="info-box">
            <p style="margin: 0; white-space: pre-wrap; font-size: 16px; line-height: 1.6;">{message}</p>
        </div>
        
        <p>Visit your dashboard to stay updated with the latest course information and announcements:</p>
        
        <div class="button-container">
            <a href="{dashboard_url}" class="button">Go to Dashboard</a>
        </div>
    """
    
    html = get_base_template(f"📢 {title}", content, "#049ad1")
    
    text = f"""
📢 {title}

Hi {full_name},

You have a new notification from Financially Fit World:

{message}

Visit your dashboard to stay updated:
{dashboard_url}

---
Financially Fit World
© 2024 Financially Fit World. All rights reserved.
"""
    
    return html, text
