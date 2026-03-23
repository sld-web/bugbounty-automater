"""Slack notification API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.slack import SlackService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class SlackMessageRequest(BaseModel):
    message: str
    channel: Optional[str] = None
    blocks: Optional[list] = None


class SlackMessageResponse(BaseModel):
    success: bool
    message: str


class SlackConfigResponse(BaseModel):
    configured: bool
    has_bot_token: bool
    has_webhook_url: bool
    channel: str


@router.get("/slack/config", response_model=SlackConfigResponse)
async def get_slack_config():
    """Get Slack configuration status."""
    slack = SlackService()
    return SlackConfigResponse(
        configured=slack.is_configured,
        has_bot_token=bool(slack.token),
        has_webhook_url=bool(slack.webhook_url),
        channel=slack.channel,
    )


@router.post("/slack/send", response_model=SlackMessageResponse)
async def send_slack_message(request: SlackMessageRequest):
    """Send a message to Slack."""
    slack = SlackService()
    
    if not slack.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slack is not configured. Please set up bot token or webhook URL.",
        )
    
    channel = request.channel or slack.channel
    
    try:
        success = await slack.send_message(
            text=request.message,
            channel=channel,
            blocks=request.blocks,
        )
        
        if success:
            return SlackMessageResponse(
                success=True,
                message=f"Message sent to {channel}",
            )
        else:
            return SlackMessageResponse(
                success=False,
                message="Failed to send message",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send Slack message: {str(e)}",
        )


@router.post("/slack/approval-request", response_model=SlackMessageResponse)
async def send_approval_request_notification(
    action_type: str,
    action_description: str,
    target_name: str,
    risk_level: str = "MEDIUM",
    proposed_command: str | None = None,
):
    """Send an approval request notification to Slack."""
    slack = SlackService()
    
    if not slack.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slack is not configured",
        )
    
    try:
        success = await slack.send_approval_request(
            action_type=action_type,
            action_description=action_description,
            target_name=target_name,
            risk_level=risk_level,
            proposed_command=proposed_command,
        )
        
        if success:
            return SlackMessageResponse(
                success=True,
                message="Approval request sent to Slack",
            )
        else:
            return SlackMessageResponse(
                success=False,
                message="Failed to send notification",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send Slack notification: {str(e)}",
        )
