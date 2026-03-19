"""Email notification service."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


class EmailService:
    """Send email notifications."""

    def __init__(self):
        external_apis = get_external_apis()
        self.host = external_apis.smtp_host
        self.port = external_apis.smtp_port
        self.user = external_apis.smtp_user
        self.password = external_apis.smtp_password
        self.from_addr = external_apis.email_from

    async def send_approval_request(
        self,
        to: str,
        action_type: str,
        action_description: str,
        target_name: str,
        risk_level: str,
        proposed_command: str | None = None,
        approval_url: str | None = None,
    ) -> bool:
        """Send an approval request email."""
        subject = f"[Approval Required] {action_type}"

        html_content = f"""
        <html>
        <body>
            <h2>Approval Required</h2>
            <p><strong>Action:</strong> {action_type}</p>
            <p><strong>Target:</strong> {target_name}</p>
            <p><strong>Risk Level:</strong> {risk_level}</p>
            <p><strong>Description:</strong></p>
            <p>{action_description}</p>
            {f'<p><strong>Proposed Command:</strong></p><pre>{proposed_command}</pre>' if proposed_command else ''}
            {f'<p><a href="{approval_url}">Review and Approve</a></p>' if approval_url else ''}
        </body>
        </html>
        """

        return await self.send(
            to=to,
            subject=subject,
            html_content=html_content,
        )

    async def send_finding_alert(
        self,
        to: str,
        title: str,
        severity: str,
        target: str,
        description: str,
    ) -> bool:
        """Send a new finding alert email."""
        subject = f"[{severity}] New Finding: {title}"

        html_content = f"""
        <html>
        <body>
            <h2>New Security Finding</h2>
            <p><strong>Severity:</strong> {severity}</p>
            <p><strong>Title:</strong> {title}</p>
            <p><strong>Target:</strong> {target}</p>
            <p><strong>Description:</strong></p>
            <p>{description}</p>
        </body>
        </html>
        """

        return await self.send(
            to=to,
            subject=subject,
            html_content=html_content,
        )

    async def send(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send an email."""
        if not self.user or not self.password:
            logger.warning("Email not configured, skipping notification")
            return False

        if not text_content:
            text_content = html_content.replace("<", "").replace(">", "")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.from_addr
        message["To"] = to

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )
            logger.info(f"Email sent to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
