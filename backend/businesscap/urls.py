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
    LLMQueryView, VectorSearchAPIView
)

schema_view = get_schema_view(
    openapi.Info(
        title="Business Capability Map API",
        default_version='v1',
        description="AI-Powered Business Capability Map Management System API",
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
    path('api/capabilities/search/', VectorSearchAPIView.as_view(), {'content_type': 'capabilities'}, name='capability-search'),
    path('api/business-goals/search/', VectorSearchAPIView.as_view(), {'content_type': 'business-goals'}, name='business-goal-search'),
    path('api/recommendations/search/', VectorSearchAPIView.as_view(), {'content_type': 'recommendations'}, name='recommendation-search'),
    path('api/llm/query/', LLMQueryView.as_view(), name='llm-query'),
    path('api/', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
