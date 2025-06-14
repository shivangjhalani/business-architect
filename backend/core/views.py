from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import google.generativeai as genai
import os
import json
import PyPDF2
import io
import logging
from django.utils import timezone

from .models import Capability, BusinessGoal, CapabilityRecommendation
from .serializers import (
    CapabilitySerializer, CapabilityListSerializer,
    BusinessGoalSerializer, BusinessGoalDetailSerializer,
    CapabilityRecommendationSerializer,
    LLMQuerySerializer, LLMResponseSerializer
)
from .constants import API_TO_MODEL_CONTENT_TYPE, VALID_API_CONTENT_TYPES, ContentTypes

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')
logger = logging.getLogger(__name__)


class CapabilityViewSet(viewsets.ModelViewSet):
    queryset = Capability.objects.all()
    serializer_class = CapabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'status', 'parent', 'strategic_importance']
    search_fields = ['name', 'description', 'owner']
    ordering_fields = ['name', 'level', 'created_at', 'strategic_importance']
    ordering = ['level', 'name']

    def get_serializer_class(self):
        return CapabilityListSerializer if self.action == 'list' else CapabilitySerializer

    def get_queryset(self):
        queryset = Capability.objects.all()
        params = self.request.query_params
        
        if params.get('root_only', '').lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        if parent_id := params.get('parent_id'):
            queryset = queryset.filter(parent_id=parent_id)
        
        return queryset

    def destroy(self, request, *args, **kwargs):
        capability = self.get_object()
        
        if capability.children.exists():
            return Response(
                {'error': 'Cannot delete capability with children. Please reassign or delete children first.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        capability.status = 'ARCHIVED'
        capability.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        capability = self.get_object()
        
        if capability.children.exists():
            return Response(
                {'error': 'Cannot permanently delete capability with children.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recommendations = CapabilityRecommendation.objects.filter(target_capability=capability)
        if recommendations.exists():
            return Response(
                {'error': f'Cannot delete capability referenced by {recommendations.count()} recommendation(s).'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        capability.delete()
        return Response({'message': f'Capability "{capability.name}" has been permanently deleted.'})

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        capability = self.get_object()
        children = capability.children.all()
        serializer = CapabilityListSerializer(children, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        capability = self.get_object()
        ancestors = []
        current = capability.parent
        while current:
            ancestors.append(current)
            current = current.parent
        
        serializer = CapabilityListSerializer(ancestors, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        capability = self.get_object()
        descendants = []
        
        def collect_children(cap):
            for child in cap.children.all():
                descendants.append(child)
                collect_children(child)
        
        collect_children(capability)
        serializer = CapabilityListSerializer(descendants, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        from .vector_manager import vector_manager
        
        capability = self.get_object()
        limit = min(int(request.GET.get('limit', 5)), 20)
        threshold = float(request.GET.get('threshold', 0.6))
        
        try:
            query_text = f"{capability.name} {capability.description}"
            results = vector_manager.search_similar(
                content_type=ContentTypes.CAPABILITY,
                query_text=query_text,
                k=limit + 1,
                threshold=threshold
            )
            
            filtered_results = [r for r in results if r['object_id'] != str(capability.id)][:limit]
            
            return Response({
                'similar_capabilities': filtered_results,
                'query_capability': {'id': str(capability.id), 'name': capability.name}
            })
            
        except Exception as e:
            return Response({'error': f'Similar search failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessGoalViewSet(viewsets.ModelViewSet):
    queryset = BusinessGoal.objects.all()
    serializer_class = BusinessGoalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['submitted_at', 'title']
    ordering = ['-submitted_at']

    def get_serializer_class(self):
        return BusinessGoalDetailSerializer if self.action == 'retrieve' else BusinessGoalSerializer

    def destroy(self, request, *args, **kwargs):
        goal = self.get_object()
        goal.status = 'CLOSED'
        goal.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        goal = self.get_object()
        goal.delete()
        return Response({'message': f'Business goal "{goal.title}" has been permanently deleted.'})

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        business_goal = self.get_object()
        
        if business_goal.status != 'PENDING_ANALYSIS':
            return Response({'error': 'Goal must be in PENDING_ANALYSIS status'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            goal_text = self._prepare_goal_text(business_goal)
            capability_context = self._get_capability_context()
            recommendations_data = self._generate_ai_recommendations(goal_text, capability_context)
            created_count = self._create_recommendations(business_goal, recommendations_data)
            
            business_goal.status = 'ANALYZED'
            business_goal.save()
            
            return Response({
                'status': 'success',
                'recommendations_created': created_count,
                'summary': f'Analysis complete. Generated {created_count} recommendations.'
            })
            
        except Exception as e:
            logger.error(f"Error analyzing business goal {business_goal.id}: {e}")
            return Response({'error': f'Analysis failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        business_goal = self.get_object()
        recommendations = CapabilityRecommendation.objects.filter(business_goal=business_goal)
        
        # Apply pagination
        page = self.paginate_queryset(recommendations)
        if page is not None:
            serializer = CapabilityRecommendationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CapabilityRecommendationSerializer(recommendations, many=True)
        return Response({
            'count': recommendations.count(),
            'results': serializer.data
        })

    def _prepare_goal_text(self, business_goal):
        text = f"Title: {business_goal.title}\nDescription: {business_goal.description}"
        
        if business_goal.pdf_file:
            try:
                pdf_text = self._extract_pdf_text(business_goal.pdf_file)
                text += f"\n\nPDF Content:\n{pdf_text[:2000]}"
            except Exception as e:
                logger.warning(f"Could not extract PDF text: {e}")
        
        return text

    def _extract_pdf_text(self, pdf_file):
        pdf_file.seek(0)
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        return ' '.join([page.extract_text() for page in reader.pages])

    def _get_capability_context(self):
        capabilities = Capability.objects.filter(status__in=['CURRENT', 'PROPOSED']).values(
            'id', 'name', 'description', 'level', 'strategic_importance'
        )
        # Convert UUID objects to strings for JSON serialization
        capability_list = []
        for cap in capabilities:
            cap_dict = dict(cap)
            cap_dict['id'] = str(cap_dict['id'])  # Convert UUID to string
            capability_list.append(cap_dict)
        return capability_list

    def _generate_ai_recommendations(self, goal_text, capability_context):
        prompt = f"""
        Analyze this business goal and suggest capability recommendations:

        BUSINESS GOAL:
        {goal_text}

        CURRENT CAPABILITIES:
        {json.dumps(capability_context, indent=2)}

        Provide recommendations in JSON format:
        {{
            "recommendations": [
                {{
                    "type": "ADD_CAPABILITY|MODIFY_CAPABILITY|STRENGTHEN_CAPABILITY",
                    "target_capability_id": "uuid or null",
                    "proposed_name": "string or null",
                    "proposed_description": "string or null", 
                    "proposed_parent_id": "uuid or null",
                    "rationale": "string"
                }}
            ]
        }}
        """
        
        response = model.generate_content(prompt)
        return self._parse_ai_response(response.text)

    def _parse_ai_response(self, response_text):
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            
            data = json.loads(json_str)
            return data.get('recommendations', [])
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return []

    def _create_recommendations(self, business_goal, recommendations_data):
        created_count = 0
        
        for rec_data in recommendations_data:
            try:
                CapabilityRecommendation.objects.create(
                    business_goal=business_goal,
                    recommendation_type=rec_data.get('type', 'ADD_CAPABILITY'),
                    target_capability_id=rec_data.get('target_capability_id'),
                    proposed_name=rec_data.get('proposed_name'),
                    proposed_description=rec_data.get('proposed_description'),
                    proposed_parent_id=rec_data.get('proposed_parent_id'),
                    additional_details=rec_data.get('rationale', ''),
                    status='PENDING',
                    recommended_by_ai_at=timezone.now()
                )
                created_count += 1
            except Exception as e:
                logger.error(f"Error creating recommendation: {e}")
        
        return created_count


class CapabilityRecommendationViewSet(viewsets.ModelViewSet):
    queryset = CapabilityRecommendation.objects.all()
    serializer_class = CapabilityRecommendationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['recommendation_type', 'status', 'business_goal', 'target_capability']
    ordering_fields = ['recommended_by_ai_at', 'status']
    ordering = ['-recommended_by_ai_at']

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        recommendation = self.get_object()
        
        if recommendation.status != 'PENDING':
            return Response({'error': 'Only pending recommendations can be applied'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self._apply_recommendation(recommendation)
            
            recommendation.status = 'APPLIED'
            recommendation.applied_at = timezone.now()
            recommendation.save()
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error applying recommendation {recommendation.id}: {e}")
            return Response({'error': f'Failed to apply recommendation: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        recommendation = self.get_object()
        
        if recommendation.status != 'PENDING':
            return Response({'error': 'Only pending recommendations can be rejected'}, status=status.HTTP_400_BAD_REQUEST)
        
        recommendation.status = 'REJECTED'
        recommendation.save()
        
        return Response({'status': 'success', 'message': 'Recommendation rejected'})

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        recommendation = self.get_object()
        recommendation_title = f"{recommendation.recommendation_type}: {recommendation.proposed_name or 'N/A'}"
        recommendation.delete()
        return Response({'message': f'Recommendation "{recommendation_title}" has been permanently deleted.'})

    def _apply_recommendation(self, recommendation):
        if recommendation.recommendation_type == 'ADD_CAPABILITY':
            return self._apply_add_capability(recommendation)
        elif recommendation.recommendation_type == 'MODIFY_CAPABILITY':
            return self._apply_modify_capability(recommendation)
        elif recommendation.recommendation_type == 'STRENGTHEN_CAPABILITY':
            return self._apply_strengthen_capability(recommendation)
        else:
            raise ValueError(f"Unsupported recommendation type: {recommendation.recommendation_type}")

    def _apply_add_capability(self, recommendation):
        capability = Capability.objects.create(
            name=recommendation.proposed_name,
            description=recommendation.proposed_description or '',
            parent_id=recommendation.proposed_parent_id,
            status='PROPOSED',
            strategic_importance='MEDIUM'
        )
        
        return {
            'status': 'success',
            'action_taken': 'capability_created',
            'capability_id': str(capability.id),
            'message': f'Created new capability: {capability.name}'
        }

    def _apply_modify_capability(self, recommendation):
        if not recommendation.target_capability:
            raise ValueError("Target capability required for modification")
        
        capability = recommendation.target_capability
        
        if recommendation.proposed_name:
            capability.name = recommendation.proposed_name
        if recommendation.proposed_description:
            capability.description = recommendation.proposed_description
        if recommendation.proposed_parent_id:
            capability.parent_id = recommendation.proposed_parent_id
        
        capability.save()
        
        return {
            'status': 'success',
            'action_taken': 'capability_modified',
            'capability_id': str(capability.id),
            'message': f'Modified capability: {capability.name}'
        }

    def _apply_strengthen_capability(self, recommendation):
        if not recommendation.target_capability:
            raise ValueError("Target capability required for strengthening")
        
        capability = recommendation.target_capability
        
        if recommendation.additional_details:
            notes = capability.notes or ''
            capability.notes = f"{notes}\n\nStrengthening recommendation: {recommendation.additional_details}".strip()
            capability.save()
        
        return {
            'status': 'success',
            'action_taken': 'capability_strengthened',
            'capability_id': str(capability.id),
            'message': f'Strengthened capability: {capability.name}'
        }


class LLMQueryView(APIView):
    
    def post(self, request):
        serializer = LLMQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        context = serializer.validated_data.get('context', '')
        
        try:
            from .vector_manager import vector_manager
            vector_context = self._get_vector_context(query, vector_manager)
            enhanced_context = self._build_enhanced_context(context, vector_context)
            
            prompt = f"""
            Context: {enhanced_context}
            
            Question: {query}
            
            Provide a helpful answer based on the context provided.
            """
            
            response = model.generate_content(prompt)
            
            response_data = {
                'answer': response.text,
                'query': query,
                'context_used': enhanced_context[:500] + '...' if len(enhanced_context) > 500 else enhanced_context,
                'vector_context': vector_context
            }
            
            return Response(LLMResponseSerializer(response_data).data)
            
        except Exception as e:
            logger.error(f"Error processing LLM query: {e}")
            return Response({'error': f'Query processing failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_vector_context(self, query, vector_manager):
        try:
            capabilities = vector_manager.search_similar(ContentTypes.CAPABILITY, query, k=3, threshold=0.5)
            goals = vector_manager.search_similar(ContentTypes.BUSINESS_GOAL, query, k=2, threshold=0.5)
            recommendations = vector_manager.search_similar(ContentTypes.RECOMMENDATION, query, k=2, threshold=0.5)
            
            return {
                'similar_capabilities': capabilities,
                'similar_goals': goals,
                'similar_recommendations': recommendations,
                'context_enhancement': f"Found {len(capabilities)} relevant capabilities, {len(goals)} goals, {len(recommendations)} recommendations"
            }
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return {'similar_capabilities': [], 'similar_goals': [], 'similar_recommendations': [], 'context_enhancement': 'Vector search unavailable'}

    def _build_enhanced_context(self, base_context, vector_context):
        context_parts = [base_context] if base_context else []
        
        if vector_context['similar_capabilities']:
            cap_context = self._build_capability_summary(vector_context['similar_capabilities'])
            context_parts.append(f"Relevant Capabilities:\n{cap_context}")
        
        return '\n\n'.join(context_parts)

    def _build_capability_summary(self, capabilities):
        summaries = []
        for cap in capabilities[:3]:
            summaries.append(f"- {cap.get('name', 'Unknown')}: {cap.get('description', 'No description')}")
        return '\n'.join(summaries)


class VectorSearchAPIView(APIView):
    
    def post(self, request, content_type):
        if content_type not in VALID_API_CONTENT_TYPES:
            return Response({'error': f'Invalid content type: {content_type}'}, status=status.HTTP_400_BAD_REQUEST)
        
        query = request.data.get('query', '')
        limit = min(int(request.data.get('limit', 10)), 50)
        threshold = float(request.data.get('threshold', 0.5))
        
        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .vector_manager import vector_manager
            model_content_type = API_TO_MODEL_CONTENT_TYPE[content_type]
            
            results = vector_manager.search_similar(
                content_type=model_content_type,
                query_text=query,
                k=limit,
                threshold=threshold
            )
            
            return Response({
                'results': results,
                'query': query,
                'total_results': len(results)
            })
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return Response({'error': f'Search failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)