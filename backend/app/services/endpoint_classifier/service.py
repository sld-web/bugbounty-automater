"""Service for classifying endpoints during target processing."""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.target import Target
from app.services.endpoint_classifier.classifier import endpoint_classifier
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EndpointClassificationService:
    """Service to classify endpoints for targets."""

    async def classify_target_endpoints(
        self, 
        target_id: str, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Classify all endpoints for a given target.
        
        Args:
            target_id: The target's UUID
            db: Database session
            
        Returns:
            Classification results
        """
        try:
            # Get the target
            result = await db.execute(
                select(Target).where(Target.id == target_id)
            )
            target = result.scalar_one_or_none()
            
            if not target:
                logger.error(f"Target not found: {target_id}")
                return {
                    'error': f'Target not found: {target_id}',
                    'total_endpoints': 0,
                    'classified': {}
                }
            
            # Classify endpoints
            classification_result = endpoint_classifier.classify_target_endpoints(target)
            
            # Save to database
            await db.commit()
            await db.refresh(target)
            
            logger.info(
                f"Classified {classification_result['total_endpoints']} endpoints "
                f"for target {target.name} as {classification_result.get('primary_type', 'unknown')}"
            )
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Error classifying endpoints for target {target_id}: {e}")
            await db.rollback()
            return {
                'error': str(e),
                'total_endpoints': 0,
                'classified': {}
            }

    async def classify_single_endpoint(
        self,
        endpoint_url: str,
        method: str = "GET",
        response_status: Optional[int] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify a single endpoint.
        
        Returns:
            Classification result
        """
        return endpoint_classifier.classify_endpoint(
            endpoint=endpoint_url,
            method=method,
            response_status=response_status,
            response_headers=response_headers,
            response_body=response_body
        )


# Global instance
endpoint_classification_service = EndpointClassificationService()