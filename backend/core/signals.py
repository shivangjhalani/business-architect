from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
import logging
from .models import Capability, BusinessGoal, CapabilityRecommendation
from .vector_manager import vector_manager
from .constants import ContentTypes

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Capability)
def capability_post_save(sender, instance, created, **kwargs):
    """Generate or update vector embedding when a Capability is saved."""
    try:
        # Only create embeddings for active capabilities
        if instance.status in ['CURRENT', 'PROPOSED']:
            text = f"{instance.name} {instance.description}"
            
            # Use transaction.on_commit to ensure the model is saved before embedding
            def create_embedding():
                try:
                    vector_manager.add_vector(ContentTypes.CAPABILITY, str(instance.id), text)
                    logger.info(f"{'Created' if created else 'Updated'} embedding for capability: {instance.name}")
                except Exception as e:
                    logger.error(f"Error creating embedding for capability {instance.id}: {e}")
            
            transaction.on_commit(create_embedding)
        else:
            # Remove embedding for deprecated/archived capabilities
            def remove_embedding():
                try:
                    vector_manager.remove_vector(ContentTypes.CAPABILITY, str(instance.id))
                    logger.info(f"Removed embedding for deprecated capability: {instance.name}")
                except Exception as e:
                    logger.error(f"Error removing embedding for capability {instance.id}: {e}")
            
            transaction.on_commit(remove_embedding)
    
    except Exception as e:
        logger.error(f"Error in capability_post_save signal for {instance.id}: {e}")

@receiver(post_delete, sender=Capability)
def capability_post_delete(sender, instance, **kwargs):
    """Remove vector embedding when a Capability is deleted."""
    try:
        vector_manager.remove_vector(ContentTypes.CAPABILITY, str(instance.id))
        logger.info(f"Removed embedding for deleted capability: {instance.name}")
    except Exception as e:
        logger.error(f"Error removing embedding for deleted capability {instance.id}: {e}")

@receiver(post_save, sender=BusinessGoal)
def business_goal_post_save(sender, instance, created, **kwargs):
    """Generate or update vector embedding when a BusinessGoal is saved."""
    try:
        text = f"{instance.title} {instance.description}"
        
        def create_embedding():
            try:
                vector_manager.add_vector(ContentTypes.BUSINESS_GOAL, str(instance.id), text)
                logger.info(f"{'Created' if created else 'Updated'} embedding for business goal: {instance.title}")
            except Exception as e:
                logger.error(f"Error creating embedding for business goal {instance.id}: {e}")
        
        transaction.on_commit(create_embedding)
    
    except Exception as e:
        logger.error(f"Error in business_goal_post_save signal for {instance.id}: {e}")

@receiver(post_delete, sender=BusinessGoal)
def business_goal_post_delete(sender, instance, **kwargs):
    """Remove vector embedding when a BusinessGoal is deleted."""
    try:
        vector_manager.remove_vector(ContentTypes.BUSINESS_GOAL, str(instance.id))
        logger.info(f"Removed embedding for deleted business goal: {instance.title}")
    except Exception as e:
        logger.error(f"Error removing embedding for deleted business goal {instance.id}: {e}")

@receiver(post_save, sender=CapabilityRecommendation)
def recommendation_post_save(sender, instance, created, **kwargs):
    """Generate or update vector embedding when a CapabilityRecommendation is saved."""
    try:
        # Create a comprehensive text representation of the recommendation
        text_parts = [
            instance.get_recommendation_type_display(),
            instance.proposed_name or '',
            instance.proposed_description or '',
            instance.additional_details or '',
            instance.business_goal.title
        ]
        text = ' '.join(filter(None, text_parts))
        
        def create_embedding():
            try:
                vector_manager.add_vector(ContentTypes.RECOMMENDATION, str(instance.id), text)
                logger.info(f"{'Created' if created else 'Updated'} embedding for recommendation: {instance}")
            except Exception as e:
                logger.error(f"Error creating embedding for recommendation {instance.id}: {e}")
        
        transaction.on_commit(create_embedding)
    
    except Exception as e:
        logger.error(f"Error in recommendation_post_save signal for {instance.id}: {e}")

@receiver(post_delete, sender=CapabilityRecommendation)
def recommendation_post_delete(sender, instance, **kwargs):
    """Remove vector embedding when a CapabilityRecommendation is deleted."""
    try:
        vector_manager.remove_vector(ContentTypes.RECOMMENDATION, str(instance.id))
        logger.info(f"Removed embedding for deleted recommendation: {instance}")
    except Exception as e:
        logger.error(f"Error removing embedding for deleted recommendation {instance.id}: {e}") 