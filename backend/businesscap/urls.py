"""
URL configuration for businesscap project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from core.views import (
    CapabilityViewSet, BusinessGoalViewSet, CapabilityRecommendationViewSet, 
    LLMQueryView, VectorSearchAPIView, SimilarObjectsAPIView, 
    VectorManagementAPIView
)

# API Documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Business Capability Map API",
        default_version='v1',
        description="""
        AI-Powered Business Capability Map Management System API
        
        This API provides endpoints for:
        - Managing business capabilities with hierarchical structure
        - Submitting and analyzing business goals using AI
        - Managing AI-generated recommendations
        - Interactive AI assistant for capability questions
        
        ## Authentication
        Currently using AllowAny permissions for development.
        
        ## File Uploads
        PDF files up to 10MB are supported for business goal submissions.
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@businesscap.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

router = DefaultRouter()
router.register(r'capabilities', CapabilityViewSet)
router.register(r'business-goals', BusinessGoalViewSet)
router.register(r'recommendations', CapabilityRecommendationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Vec search
    path('api/capabilities/search/', VectorSearchAPIView.as_view(), {'content_type': 'capabilities'}, name='capability-search'),
    path('api/business-goals/search/', VectorSearchAPIView.as_view(), {'content_type': 'business_goals'}, name='business-goal-search'),
    path('api/recommendations/search/', VectorSearchAPIView.as_view(), {'content_type': 'recommendations'}, name='recommendation-search'),
    
    # Similar objects
    path('api/capabilities/<uuid:object_id>/similar/', SimilarObjectsAPIView.as_view(), {'content_type': 'capabilities'}, name='capability-similar'),
    path('api/business-goals/<uuid:object_id>/similar/', SimilarObjectsAPIView.as_view(), {'content_type': 'business_goals'}, name='business-goal-similar'),
    path('api/recommendations/<uuid:object_id>/similar/', SimilarObjectsAPIView.as_view(), {'content_type': 'recommendations'}, name='recommendation-similar'),
    
    # LLM and AI
    path('api/llm/query/', LLMQueryView.as_view(), name='llm-query'),
    
    # Vector management
    path('api/vectors/status/', VectorManagementAPIView.as_view(), name='vector-status'),
    path('api/vectors/rebuild/', VectorManagementAPIView.as_view(), name='vector-rebuild'),
    path('api/vectors/optimize/', VectorManagementAPIView.as_view(), name='vector-optimize'),
    
    # DRF router
    path('api/', include(router.urls)),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-root'),  # Default to Swagger
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
