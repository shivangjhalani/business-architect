from django.contrib import admin
from django.utils.html import format_html
from .models import Capability, BusinessGoal, CapabilityRecommendation


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'status', 'strategic_importance', 'owner', 'created_at']
    list_filter = ['status', 'strategic_importance', 'level', 'created_at']
    search_fields = ['name', 'description', 'owner']
    list_editable = ['status', 'strategic_importance', 'owner']
    ordering = ['level', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'level'),
            'description': 'Level is automatically calculated based on parent'
        }),
        ('Classification', {
            'fields': ('status', 'strategic_importance', 'owner')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['level', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


@admin.register(BusinessGoal)
class BusinessGoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'submitted_at', 'recommendations_count_display', 'has_pdf']
    list_filter = ['status', 'submitted_at']
    search_fields = ['title', 'description']
    list_editable = ['status']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Goal Information', {
            'fields': ('title', 'description')
        }),
        ('Documentation', {
            'fields': ('pdf_file',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )
    
    readonly_fields = ['submitted_at']
    
    def recommendations_count_display(self, obj):
        count = obj.recommendations_count
        if count > 0:
            return format_html(
                '<span style="color: green;">{} recommendations</span>',
                count
            )
        return "No recommendations"
    recommendations_count_display.short_description = "Recommendations"
    
    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    has_pdf.boolean = True
    has_pdf.short_description = "PDF Attached"


@admin.register(CapabilityRecommendation)
class CapabilityRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'business_goal', 
        'recommendation_type', 
        'target_capability', 
        'status', 
        'recommended_by_ai_at',
        'applied_at'
    ]
    list_filter = [
        'recommendation_type', 
        'status', 
        'recommended_by_ai_at', 
        'business_goal__status'
    ]
    search_fields = [
        'business_goal__title', 
        'target_capability__name', 
        'proposed_name',
        'additional_details'
    ]
    list_editable = ['status']
    ordering = ['-recommended_by_ai_at']
    
    fieldsets = (
        ('Recommendation Details', {
            'fields': ('business_goal', 'recommendation_type', 'status')
        }),
        ('Target Information', {
            'fields': ('target_capability',),
            'description': 'For modify, delete, or strengthen operations'
        }),
        ('Proposed Changes', {
            'fields': ('proposed_name', 'proposed_description', 'proposed_parent'),
            'description': 'For add or modify operations'
        }),
        ('AI Analysis', {
            'fields': ('additional_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('recommended_by_ai_at', 'applied_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['recommended_by_ai_at', 'applied_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'business_goal', 
            'target_capability', 
            'proposed_parent'
        )


# Admin site customization
admin.site.site_header = "Business Capability Management"
admin.site.site_title = "Business Cap Admin"
admin.site.index_title = "Manage Business Capabilities"
