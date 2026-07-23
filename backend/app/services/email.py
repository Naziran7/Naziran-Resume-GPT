import logging
import resend
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        if self.api_key:
            resend.api_key = self.api_key
            logger.info("Resend Email client initialized.")
        else:
            logger.warning("RESEND_API_KEY not configured. Email Service will run in mock/log-only mode.")

    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send a password reset email using Resend or log it to the console if not configured."""
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - NaziranGPT"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #2b6cb0; text-align: center;">NaziranGPT Security</h2>
            <p>Hello,</p>
            <p>We received a request to reset the password for your NaziranGPT account. If you did not make this request, you can safely ignore this email.</p>
            <p>To reset your password, please click the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #3182ce; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Reset Password</a>
            </div>
            <p>Or copy and paste this link into your browser address bar:</p>
            <p style="word-break: break-all; color: #4a5568;"><a href="{reset_link}">{reset_link}</a></p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;" />
            <p style="font-size: 11px; color: #718096; text-align: center;">NaziranGPT &bull; AI-Powered Career Intelligence Platform</p>
        </div>
        """
        
        if self.api_key:
            try:
                # Send email using resend.Emails.send async boundary (wrapped in thread since resend is blocking)
                import asyncio
                params = {
                    "from": "NaziranGPT Security <onboarding@resend.dev>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                }
                
                # Execute blocking Resend call in asyncio thread pool
                response = await asyncio.to_thread(resend.Emails.send, params)
                logger.info(f"Password reset email sent via Resend to {to_email}. Response ID: {response.get('id')}")
                return True
            except Exception as e:
                logger.error(f"Resend failed to send password reset email to {to_email}: {str(e)}")
                return False
        else:
            # Mock print to console
            logger.warning("--- EMAIL MOCK LOG ---")
            logger.warning(f"To: {to_email}")
            logger.warning(f"Subject: {subject}")
            logger.warning(f"Reset Link: {reset_link}")
            logger.warning("----------------------")
            return True
