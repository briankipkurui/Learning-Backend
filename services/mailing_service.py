import asyncio
from typing import List, Optional, Dict, Any
import logging
import resend
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class EmailService:
    """Email service using Resend API for sending emails with Jinja2 templating support"""
    
    def __init__(self):
        """
        Initialize email service with Resend and Jinja2
        """
        self.from_email = "hello@careerelevate.ai" # os.getenv("GMAIL_USER")
        self.display_name = "Career Elevate"
        # Set Resend API key
        resend.api_key = os.getenv("RESEND_API_KEY")
        
        # Initialize Jinja2 environment for email templates
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 email template with the given context
        
        Args:
            template_name: Name of the template file (e.g., 'otp_verification.html')
            context: Dictionary of variables to pass to the template
            
        Returns:
            str: Rendered HTML content
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using Resend API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default: False for plain text)
            cc: List of CC recipients (optional)
            bcc: List of BCC recipients (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Prepare email parameters
            email_params = {
                "from": f"{self.display_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
            }
            
            # Set body content based on type
            if is_html:
                email_params["html"] = body
            else:
                email_params["text"] = body
            
            # Add CC and BCC if provided
            if cc:
                email_params["cc"] = cc
            if bcc:
                email_params["bcc"] = bcc
            
            # Send email using Resend
            response = resend.Emails.send(email_params)
            
            logger.info(f"Email sent successfully to {to_email} via Resend. ID: {response.get('id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via Resend: {str(e)}")
            return False
    
    async def send_otp_email(
            self, 
            to_email: str, 
            otp_code: str, 
            user_name: str = "User",
            expiry_minutes: int = 15,
            show_ignore_message: bool = True
        ) -> bool:
        """
        Send OTP verification email using Jinja2 template
        
        Args:
            to_email: Recipient email
            otp_code: The OTP code to send
            user_name: User's name for personalization
            expiry_minutes: OTP expiration time in minutes (default: 15)
            show_ignore_message: Whether to show "ignore if not requested" message
            
        Returns:
            bool: True if sent successfully
        """
        try:
            subject = "Verify Your Email"
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'otp_code': otp_code,
                'expiry_minutes': expiry_minutes,
                'show_ignore_message': show_ignore_message
            }
            
            # Render template
            html_body = self.render_template('otp_verification.html', context)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=html_body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {str(e)}")
    
    async def send_welcome_email(
            self, 
            to_email: str, 
            user_name: str,
            features: Optional[List[str]] = None,
            show_cta: bool = True
        ) -> bool:
        """
        Send welcome email after successful verification using Jinja2 template
        
        Args:
            to_email: Recipient email
            user_name: User's name
            features: List of features to highlight (default: standard features)
            show_cta: Whether to show call-to-action button
            
        Returns:
            bool: True if sent successfully
        """
        try:
            subject = "Welcome to Career Elevate!"
            
            # Default features if not provided
            if features is None:
                features = [
                    "Browse our course catalog",
                    "Enroll in courses",
                    "Use our CV Analyzer to apply for your dream job",
                    "Practice for your next interview",
                    "Track your job applications with our easy to use Job Application Tracker",
                    "Join our learning community"
                ]
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'features': features,
                'show_cta': show_cta,
                'cta_url': os.getenv("UI_DOMAIN", '')
            }
            
            # Render template
            html_body = self.render_template('welcome.html', context)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=html_body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")

    async def send_password_reset_email(
            self, 
            to_email: str, 
            otp_code: str, 
            user_name: str,
            expiry_minutes: int = 10,
            show_ignore_message: bool = True
        ) -> bool:
        """
        Send password reset email with OTP using Jinja2 template
        
        Args:
            to_email: Recipient email
            otp_code: The OTP code for password reset
            user_name: User's name
            expiry_minutes: OTP expiration time in minutes (default: 10)
            show_ignore_message: Whether to show "ignore if not requested" message
            
        Returns:
            bool: True if sent successfully
        """
        try:
            subject = "Password Reset Request"
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'otp_code': otp_code,
                'expiry_minutes': expiry_minutes,
                'show_ignore_message': show_ignore_message
            }
            
            # Render template
            html_body = self.render_template('password_reset.html', context)

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=html_body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")

    async def send_course_enrollment_email(
            self, 
            to_email: str, 
            user_name: str, 
            course_title: str, 
            course_id: str,
            enrollment_date: str = "Today",
            show_cta: bool = True,
            show_tips: bool = True
        ) -> bool:
        """
        Send course enrollment confirmation email using Jinja2 template
        
        Args:
            to_email: Student email
            user_name: Student's name
            course_title: Name of the course they enrolled in
            course_id: Course identifier for generating course URL
            enrollment_date: Date of enrollment (default: "Today")
            show_cta: Whether to show "Start Learning" button
            show_tips: Whether to show study tips section
            
        Returns:
            bool: True if sent successfully
        """
        try:
            subject = f"Welcome to {course_title}! 🎉"
            
            # Default next steps - includes unlimited access to AI features
            next_steps = [
                "Access your course dashboard anytime",
                "Track your progress through each module",
                "Use unlimited CV Analysis and Interview Practice",
                "Complete assignments and quizzes",
                "Earn your certificate upon completion",
                "Connect with other students in the community"
            ]
            
            # Default study tips
            study_tips = [
                "Set aside dedicated time for learning",
                "Take notes and practice what you learn",
                "Don't hesitate to reach out if you need help",
                "Join our community discussions for support"
            ]
            
            # Prepare template context
            context = {
                'user_name': user_name.title(),
                'course_title': course_title,
                'enrollment_date': enrollment_date,
                'show_cta': show_cta,
                'course_url': f"{os.getenv('UI_DOMAIN', '')}/learn/{course_id}",
                'next_steps': next_steps,
                'show_tips': show_tips,
                'study_tips': study_tips
            }
            
            # Render template
            html_body = self.render_template('course_enrollment.html', context)

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=html_body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send course enrollment email to {to_email} for course {course_title}: {str(e)}")

    
    async def send_bulk_emails(self, emails: List[dict]) -> dict:
        """
        Send multiple emails concurrently
        
        Args:
            emails: List of dict with keys: to_email, subject, body, is_html (optional)
            
        Returns:
            dict: Results summary with success/failure counts
        """
        tasks = []
        for email_data in emails:
            task = self.send_email(
                to_email=email_data['to_email'],
                subject=email_data['subject'],
                body=email_data['body'],
                is_html=email_data.get('is_html', False)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for result in results if result is True)
        failure_count = len(results) - success_count
        
        return {
            "total": len(emails),
            "success": success_count,
            "failed": failure_count,
            "success_rate": f"{(success_count/len(emails)*100):.1f}%"
        }
    
    async def send_course_completion_email(
            self,
            to_email: str,
            user_name: str,
            course_title: str,
            certificate_url: str = None,
            has_certificate: bool = True
        ) -> bool:
        """
        Send course completion congratulations email
        
        Args:
            to_email: Student email
            user_name: Student's name
            course_title: Name of the completed course
            certificate_url: URL to download the certificate (if available)
            has_certificate: Whether certificate was generated
            
        Returns:
            bool: True if sent successfully
        """
        try:
            subject = f"🎉 Congratulations! You've Completed {course_title}"
            
            # Completion achievements
            achievements = [
                "Completed all course modules",
                "Mastered the course material",
                "Earned your completion certificate" if has_certificate else "Finished all lessons"
            ]
            
            # Next steps after completion
            next_steps = [
                "Download and share your certificate" if has_certificate else "Review your progress",
                "Explore more courses to continue learning",
                "Connect with other graduates in our community"
            ]
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'course_title': course_title,
                'has_certificate': has_certificate,
                'certificate_url': certificate_url,
                'achievements': achievements,
                'next_steps': next_steps,
                'completion_date': 'today',
                'show_share_buttons': has_certificate,
                'platform_url': os.getenv('UI_DOMAIN', '')
            }
            
            # Render template (create course_completion.html template separately)
            html_body = self.render_template('course_completion.html', context)

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=html_body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"Failed to send course completion email to {to_email} for course {course_title}: {str(e)}")
            return False