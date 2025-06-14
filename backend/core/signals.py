from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Capability, BusinessGoal, CapabilityRecommendation
from .constants import ContentTypes


@receiver(post_save, sender=Capability)
def create_or_update_capability_vector(sender, instance, created, **kwargs):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Signal triggered for capability: {instance.name}, status: {instance.status}, created: {created}")
    
    if instance.status in ['CURRENT', 'PROPOSED']:
        from .vector_manager import vector_manager
        text = f"{instance.name} {instance.description}"
        success = vector_manager.add_vector(ContentTypes.CAPABILITY, str(instance.id), text)
        logger.info(f"Vector addition for capability '{instance.name}': {'success' if success else 'failed'}")
    elif instance.status in ['DEPRECATED', 'ARCHIVED']:
        from .vector_manager import vector_manager
        success = vector_manager.remove_vector(ContentTypes.CAPABILITY, str(instance.id))
        logger.info(f"Vector removal for capability '{instance.name}': {'success' if success else 'failed'}")


@receiver(post_delete, sender=Capability)
def delete_capability_vector(sender, instance, **kwargs):
    from .vector_manager import vector_manager
    vector_manager.remove_vector(ContentTypes.CAPABILITY, str(instance.id))


@receiver(post_save, sender=BusinessGoal)
def create_or_update_business_goal_vector(sender, instance, created, **kwargs):
    from .vector_manager import vector_manager
    text = f"{instance.title} {instance.description}"
    vector_manager.add_vector(ContentTypes.BUSINESS_GOAL, str(instance.id), text)


@receiver(post_delete, sender=BusinessGoal)
def delete_business_goal_vector(sender, instance, **kwargs):
    from .vector_manager import vector_manager
    vector_manager.remove_vector(ContentTypes.BUSINESS_GOAL, str(instance.id))


@receiver(post_save, sender=CapabilityRecommendation)
def create_or_update_recommendation_vector(sender, instance, created, **kwargs):
    from .vector_manager import vector_manager
    
    text_parts = [
        instance.get_recommendation_type_display(),
        instance.proposed_name or '',
        instance.proposed_description or '',
        instance.additional_details or ''
    ]
    text = ' '.join(filter(None, text_parts))
    
    vector_manager.add_vector(ContentTypes.RECOMMENDATION, str(instance.id), text)


@receiver(post_delete, sender=CapabilityRecommendation)
def delete_recommendation_vector(sender, instance, **kwargs):
    from .vector_manager import vector_manager
    vector_manager.remove_vector(ContentTypes.RECOMMENDATION, str(instance.id)) 