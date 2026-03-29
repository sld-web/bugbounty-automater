"""Service for adaptive tuning of hypothesis generation based on learning metrics."""
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.target import Target
from app.models.learning import LearningMetric
from app.models.finding import Finding
from app.services.hypothesis_generator.service import hypothesis_generation_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AdaptiveTuningService:
    """Service for adapting hypothesis generation based on past success/failure."""

    def __init__(self, min_attempts: int = 3):
        self.min_attempts = min_attempts
        self.hypothesis_service = hypothesis_generation_service

    async def update_learning_metric(self, 
                                   target_id: str, 
                                   hypothesis_type: str, 
                                   success: bool,
                                   db: AsyncSession) -> None:
        """
        Update learning metrics for a hypothesis type on a target.
        
        Args:
            target_id: The target's UUID
            hypothesis_type: The type of hypothesis tested
            success: Whether the hypothesis was successful
            db: Database session
        """
        try:
            # Get existing metric
            result = await db.execute(
                select(LearningMetric).where(
                    LearningMetric.target_id == target_id,
                    LearningMetric.hypothesis_type == hypothesis_type
                )
            )
            metric = result.scalar_one_or_none()
            
            if metric:
                # Update existing metric
                if success:
                    metric.record_success()
                else:
                    metric.record_failure()
                
                await db.execute(
                    update(LearningMetric)
                    .where(LearningMetric.id == metric.id)
                    .values(
                        success_count=metric.success_count,
                        attempt_count=metric.attempt_count,
                        success_rate=metric.success_rate,
                        last_updated=metric.last_updated
                    )
                )
            else:
                # Create new metric
                new_metric = LearningMetric(
                    target_id=target_id,
                    hypothesis_type=hypothesis_type,
                    success_count=1 if success else 0,
                    attempt_count=1,
                    success_rate=1.0 if success else 0.0
                )
                db.add(new_metric)
            
            await db.commit()
            logger.info(
                f"Updated learning metric for target {target_id}, "
                f"hypothesis type {hypothesis_type}: success={success}"
            )
            
        except Exception as e:
            logger.error(f"Error updating learning metric: {e}")
            await db.rollback()

    async def get_adaptive_hypothesis_weights(self, 
                                            target_id: str,
                                            db: AsyncSession) -> Dict[str, float]:
        """
        Get weights for hypothesis types based on past performance.
        
        Returns:
            Dict mapping hypothesis type to weight (higher = more likely to be suggested)
        """
        try:
            result = await db.execute(
                select(LearningMetric).where(
                    LearningMetric.target_id == target_id,
                    LearningMetric.attempt_count >= self.min_attempts
                )
            )
            metrics = result.scalars().all()
            
            weights = defaultdict(float)
            for metric in metrics:
                # Weight is based on success rate, with a minimum weight for exploration
                # This implements a simple epsilon-greedy strategy
                base_weight = 0.1  # Minimum weight for exploration
                success_bonus = metric.success_rate * 0.9  # Up to 0.9 bonus for success
                weights[metric.hypothesis_type] = base_weight + success_bonus
            
            return dict(weights)
            
        except Exception as e:
            logger.error(f"Error getting adaptive hypothesis weights: {e}")
            return {}

    async def get_blind_spots(self, target_id: str, db: AsyncSession) -> List[str]:
        """
        Identify hypothesis types that consistently fail (potential blind spots).
        
        Returns:
            List of hypothesis types with low success rates despite multiple attempts
        """
        try:
            result = await db.execute(
                select(LearningMetric).where(
                    LearningMetric.target_id == target_id,
                    LearningMetric.attempt_count >= self.min_attempts,
                    LearningMetric.success_rate < 0.2  # Less than 20% success rate
                )
            )
            metrics = result.scalars().all()
            
            return [metric.hypothesis_type for metric in metrics]
            
        except Exception as e:
            logger.error(f"Error getting blind spots: {e}")
            return []

    async def get_recommended_hypothesis_types(self, 
                                             target_id: str,
                                             db: AsyncSession,
                                             limit: int = 5) -> List[str]:
        """
        Get recommended hypothesis types to try next based on learning.
        
        Returns:
            List of hypothesis type strings sorted by recommendation strength
        """
        try:
            # Get metrics with sufficient data
            result = await db.execute(
                select(LearningMetric).where(
                    LearningMetric.target_id == target_id,
                    LearningMetric.attempt_count >= self.min_attempts
                ).order_by(
                    LearningMetric.success_rate.desc(),
                    LearningMetric.attempt_count.desc()
                ).limit(limit)
            )
            metrics = result.scalars().all()
            
            return [metric.hypothesis_type for metric in metrics]
            
        except Exception as e:
            logger.error(f"Error getting recommended hypothesis types: {e}")
            return []

    async def integrate_with_hypothesis_generation(self, 
                                                 target: Target,
                                             db: AsyncSession) -> Dict[str, Any]:
        """
        Integrate adaptive tuning with hypothesis generation.
        
        Returns:
            Enhanced hypothesis generation results with adaptive weights
        """
        try:
            # Get base hypotheses from the hypothesis generation service
            base_hypotheses = self.hypothesis_service.generate_hypotheses_for_target(target)
            
            # Get adaptive weights
            weights = await self.get_adaptive_hypothesis_weights(target.id, db)
            
            # Get blind spots
            blind_spots = await self.get_blind_spots(target.id, db)
            
            # Get recommended types
            recommended_types = await self.get_recommended_hypothesis_types(
                target.id, db, limit=10
            )
            
            # Enhance hypotheses with adaptive information
            enhanced_hypotheses = []
            for hypothesis in base_hypotheses:
                hyp_type = hypothesis.get('type', 'UNKNOWN')
                
                # Calculate adaptive weight
                adaptive_weight = weights.get(hyp_type, 0.1)  # Default to exploration weight
                
                # Check if this is a blind spot
                is_blind_spot = hyp_type in blind_spots
                
                # Check if this is a recommended type
                is_recommended = hyp_type in recommended_types
                
                # Create enhanced hypothesis
                enhanced_hypothesis = {
                    **hypothesis,
                    'adaptive_weight': round(adaptive_weight, 3),
                    'is_blind_spot': is_blind_spot,
                    'is_recommended': is_recommended,
                    'priority_score': adaptive_weight * (2.0 if is_recommended else 1.0) * (0.5 if is_blind_spot else 1.0)
                }
                
                enhanced_hypotheses.append(enhanced_hypothesis)
            
            # Sort by priority score (descending)
            enhanced_hypotheses.sort(
                key=lambda x: x.get('priority_score', 0), 
                reverse=True
            )
            
            return {
                'hypotheses': enhanced_hypotheses,
                'adaptive_weights': weights,
                'blind_spots': blind_spots,
                'recommended_types': recommended_types,
                'total_hypotheses': len(enhanced_hypotheses)
            }
            
        except Exception as e:
            logger.error(f"Error integrating adaptive tuning with hypothesis generation: {e}")
            # Fallback to basic hypothesis generation
            base_hypotheses = self.hypothesis_service.generate_hypotheses_for_target(target)
            return {
                'hypotheses': base_hypotheses,
                'adaptive_weights': {},
                'blind_spots': [],
                'recommended_types': [],
                'total_hypotheses': len(base_hypotheses)
            }


# Global instance
adaptive_tuning_service = AdaptiveTuningService()