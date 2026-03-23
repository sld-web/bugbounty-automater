"""Slack notification service."""
import logging

import aiohttp

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


class SlackService:
    """Send notifications to Slack."""

    def __init__(self):
        external_apis = get_external_apis()
        self.token = external_apis.slack_bot_token
        self.channel = external_apis.slack_channel
        self.webhook_url = external_apis.slack_webhook_url
    
    @property
    def is_configured(self) -> bool:
        """Check if Slack is properly configured."""
        return bool(self.token) or bool(self.webhook_url)

    async def send_approval_request(
        self,
        action_type: str,
        action_description: str,
        target_name: str,
        risk_level: str,
        proposed_command: str | None = None,
        evidence: dict | None = None,
    ) -> bool:
        """Send an approval request notification to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Approval Required: {action_type}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Target:*\n{target_name}"},
                    {"type": "mrkdwn", "text": f"*Risk Level:*\n{risk_level}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{action_description}",
                },
            },
        ]

        if proposed_command:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Proposed Command:*\n```\n{proposed_command}\n```",
                    },
                }
            )

        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": "approve",
                        "value": action_type,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Deny"},
                        "style": "danger",
                        "action_id": "deny",
                        "value": action_type,
                    },
                ],
            }
        )

        return await self._send_message(blocks=blocks)

    async def send_approval_result(
        self,
        action_type: str,
        target_name: str,
        approved: bool,
        decided_by: str,
        reason: str | None = None,
    ) -> bool:
        """Send approval result notification."""
        status = "APPROVED" if approved else "DENIED"
        emoji = ":white_check_mark:" if approved else ":x:"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{status}:* {action_type}\n"
                    f"*Target:* {target_name}\n"
                    f"*By:* {decided_by}",
                },
            }
        ]

        if reason:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Reason:*\n{reason}"},
                }
            )

        return await self._send_message(blocks=blocks)

    async def send_finding(
        self,
        title: str,
        severity: str,
        target: str,
        description: str,
    ) -> bool:
        """Send a new finding notification."""
        emoji_map = {
            "CRITICAL": ":rotating_light:",
            "HIGH": ":warning:",
            "MEDIUM": ":large_yellow_circle:",
            "LOW": ":large_blue_circle:",
            "INFO": ":information_source:",
        }

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"New Finding: {title}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
                    {"type": "mrkdwn", "text": f"*Target:*\n{target}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": description},
            },
        ]

        return await self._send_message(blocks=blocks)

    async def send_phase_complete(
        self,
        phase_name: str,
        target_name: str,
        duration_seconds: int,
        findings_count: int = 0,
    ) -> bool:
        """Send phase completion notification."""
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Phase Complete:* {phase_name}\n"
                    f"*Target:* {target_name}\n"
                    f"*Duration:* {minutes}m {seconds}s\n"
                    f"*Findings:* {findings_count}",
                },
            }
        ]

        return await self._send_message(blocks=blocks)

    async def _send_message(
        self,
        text: str = "",
        blocks: list | None = None,
    ) -> bool:
        """Send a message to Slack."""
        if not self.webhook_url and not self.token:
            logger.warning("Slack not configured, skipping notification")
            return False

        if self.webhook_url:
            return await self._send_webhook(text, blocks)

        return await self._send_api(text, blocks)

    async def _send_webhook(
        self,
        text: str,
        blocks: list | None,
    ) -> bool:
        """Send via webhook."""
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to send Slack webhook: {e}")
            return False

    async def _send_api(
        self,
        text: str,
        blocks: list | None,
    ) -> bool:
        """Send via Slack API."""
        try:
            from slack_sdk import WebClient

            client = WebClient(token=self.token)
            client.chat_postMessage(
                channel=self.channel,
                text=text,
                blocks=blocks,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
