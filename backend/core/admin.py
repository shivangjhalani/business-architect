from django.contrib import admin
from .models import Capability, BusinessGoal, CapabilityRecommendation, VectorEmbedding


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'status', 'strategic_importance', 'owner']
    list_filter = ['status', 'strategic_importance', 'level']
    search_fields = ['name', 'description', 'owner']
    ordering = ['level', 'name']


@admin.register(BusinessGoal)
class BusinessGoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'submitted_at']
    list_filter = ['status']
    search_fields = ['title', 'description']
    ordering = ['-submitted_at']


@admin.register(CapabilityRecommendation)
class CapabilityRecommendationAdmin(admin.ModelAdmin):
    list_display = ['business_goal', 'recommendation_type', 'status', 'recommended_by_ai_at']
    list_filter = ['recommendation_type', 'status']
    search_fields = ['business_goal__title', 'proposed_name']
    ordering = ['-recommended_by_ai_at']


@admin.register(VectorEmbedding)
class VectorEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'object_id', 'vector_index', 'created_at']
    list_filter = ['content_type']
    search_fields = ['object_id', 'text_content']
    ordering = ['-created_at']


# Simple admin site customization
admin.site.site_header = "Business Capability Management"
admin.site.site_title = "Business Capability Admin"
