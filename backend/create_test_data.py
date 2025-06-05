#!/usr/bin/env python
"""
Script to create initial test data for the Business Capability Management system.
Run this script to populate the database with sample capabilities and business goals.
"""

import os
import sys
import django
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'businesscap.settings')
django.setup()

from core.models import Capability, BusinessGoal, CapabilityRecommendation


def create_sample_capabilities():
    """Create a hierarchical set of sample business capabilities."""
    print("Creating sample capabilities...")
    
    # Level 1 - Core Business Capabilities
    customer_mgmt = Capability.objects.create(
        name="Customer Relationship Management",
        description="Comprehensive management of customer interactions, data, and relationships throughout the customer lifecycle.",
        status="CURRENT",
        strategic_importance="CRITICAL",
        owner="Sales & Marketing"
    )
    
    product_mgmt = Capability.objects.create(
        name="Product Management",
        description="End-to-end product lifecycle management including development, launch, and optimization.",
        status="CURRENT",
        strategic_importance="CRITICAL",
        owner="Product Team"
    )
    
    operations = Capability.objects.create(
        name="Operations Management",
        description="Core operational processes including supply chain, logistics, and service delivery.",
        status="CURRENT",
        strategic_importance="HIGH",
        owner="Operations Team"
    )
    
    finance = Capability.objects.create(
        name="Financial Management",
        description="Financial planning, accounting, reporting, and regulatory compliance.",
        status="CURRENT",
        strategic_importance="CRITICAL",
        owner="Finance Team"
    )
    
    # Level 2 - Sub-capabilities under Customer Management
    customer_acquisition = Capability.objects.create(
        name="Customer Acquisition",
        description="Processes and systems for attracting and converting new customers.",
        parent=customer_mgmt,
        status="CURRENT",
        strategic_importance="HIGH",
        owner="Marketing Team"
    )
    
    customer_service = Capability.objects.create(
        name="Customer Service",
        description="Support systems and processes for existing customer needs and issues.",
        parent=customer_mgmt,
        status="CURRENT",
        strategic_importance="HIGH",
        owner="Customer Success"
    )
    
    customer_retention = Capability.objects.create(
        name="Customer Retention",
        description="Strategies and systems to maintain long-term customer relationships.",
        parent=customer_mgmt,
        status="CURRENT",
        strategic_importance="MEDIUM",
        owner="Customer Success"
    )
    
    # Level 2 - Sub-capabilities under Product Management
    product_development = Capability.objects.create(
        name="Product Development",
        description="Research, design, and development of new products and features.",
        parent=product_mgmt,
        status="CURRENT",
        strategic_importance="CRITICAL",
        owner="R&D Team"
    )
    
    product_marketing = Capability.objects.create(
        name="Product Marketing",
        description="Go-to-market strategies, positioning, and product promotion.",
        parent=product_mgmt,
        status="CURRENT",
        strategic_importance="HIGH",
        owner="Product Marketing"
    )
    
    # Level 3 - Sub-capabilities under Customer Acquisition
    digital_marketing = Capability.objects.create(
        name="Digital Marketing",
        description="Online marketing channels including social media, SEO, and digital advertising.",
        parent=customer_acquisition,
        status="CURRENT",
        strategic_importance="HIGH",
        owner="Digital Marketing"
    )
    
    lead_management = Capability.objects.create(
        name="Lead Management",
        description="Lead qualification, nurturing, and conversion processes.",
        parent=customer_acquisition,
        status="CURRENT",
        strategic_importance="MEDIUM",
        owner="Sales Team"
    )
    
    # Proposed capabilities
    ai_analytics = Capability.objects.create(
        name="AI-Powered Analytics",
        description="Advanced analytics and machine learning capabilities for business insights.",
        status="PROPOSED",
        strategic_importance="HIGH",
        owner="Technology Team",
        notes="Proposed for Q2 implementation"
    )
    
    print("✓ Created sample capabilities with hierarchical structure")
    return {
        'customer_mgmt': customer_mgmt,
        'product_mgmt': product_mgmt,
        'ai_analytics': ai_analytics
    }


def create_sample_business_goals():
    """Create sample business goals for testing AI analysis."""
    print("Creating sample business goals...")
    
    goal1 = BusinessGoal.objects.create(
        title="Improve Customer Retention by 15%",
        description="""
        Our current customer retention rate is 75%, which is below industry average. 
        We need to implement strategies and systems to improve retention to 90% within 12 months.
        
        Key objectives:
        - Implement predictive analytics to identify at-risk customers
        - Enhance customer service response times
        - Develop loyalty program
        - Improve product onboarding experience
        
        Success metrics:
        - Customer retention rate: 75% → 90%
        - Customer satisfaction score: 7.2 → 8.5
        - Support ticket resolution time: 24h → 4h
        """,
        status="PENDING_ANALYSIS"
    )
    
    goal2 = BusinessGoal.objects.create(
        title="Launch AI-Driven Product Recommendation Engine",
        description="""
        Develop and implement an AI-powered recommendation system to increase 
        cross-selling and upselling opportunities.
        
        Requirements:
        - Real-time product recommendations based on customer behavior
        - Integration with existing e-commerce platform
        - A/B testing capabilities for recommendation algorithms
        - Privacy-compliant data usage
        
        Expected outcomes:
        - 25% increase in average order value
        - 40% improvement in product discovery
        - Enhanced customer experience through personalization
        """,
        status="PENDING_ANALYSIS"
    )
    
    goal3 = BusinessGoal.objects.create(
        title="Digital Transformation of Sales Process",
        description="""
        Modernize our sales process through digital tools and automation to 
        improve efficiency and customer experience.
        
        Scope:
        - Implement CRM automation workflows
        - Digital contract management system
        - Virtual sales presentation tools
        - Real-time sales analytics dashboard
        
        Timeline: 6 months
        Budget: $500K
        Expected ROI: 200% within 18 months
        """,
        status="ANALYZED"
    )
    
    print("✓ Created sample business goals")
    return [goal1, goal2, goal3]


def create_sample_recommendations(goals, capabilities):
    """Create sample AI recommendations for testing."""
    print("Creating sample recommendations...")
    
    # Create recommendations for the analyzed goal
    analyzed_goal = None
    for goal in goals:
        if goal.status == "ANALYZED":
            analyzed_goal = goal
            break
    
    if analyzed_goal:
        # Recommendation to strengthen existing capability
        rec1 = CapabilityRecommendation.objects.create(
            business_goal=analyzed_goal,
            recommendation_type="STRENGTHEN_CAPABILITY",
            target_capability=capabilities['customer_mgmt'],
            additional_details="Enhance CRM capabilities with automation workflows to support digital sales transformation.",
            status="PENDING"
        )
        
        # Recommendation to add new capability
        rec2 = CapabilityRecommendation.objects.create(
            business_goal=analyzed_goal,
            recommendation_type="ADD_CAPABILITY",
            proposed_name="Digital Sales Tools",
            proposed_description="Comprehensive digital toolset for modern sales processes including virtual presentations, digital contracts, and automated workflows.",
            proposed_parent=capabilities['customer_mgmt'],
            additional_details="New capability needed to support digital transformation objectives with modern sales tools and processes.",
            status="PENDING"
        )
        
        # Recommendation to modify existing capability
        rec3 = CapabilityRecommendation.objects.create(
            business_goal=analyzed_goal,
            recommendation_type="MODIFY_CAPABILITY",
            target_capability=capabilities['product_mgmt'],
            proposed_description="Enhanced product management with real-time analytics dashboard and automated reporting capabilities.",
            additional_details="Modify existing product management to include advanced analytics and automation features required for digital sales process.",
            status="APPLIED"
        )
        
        print("✓ Created sample recommendations")
    

def main():
    """Main function to create all test data."""
    print("=" * 50)
    print("Creating Test Data for Business Capability Management")
    print("=" * 50)
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing test data...")
        CapabilityRecommendation.objects.all().delete()
        BusinessGoal.objects.all().delete()
        Capability.objects.all().delete()
        
        # Create test data
        capabilities = create_sample_capabilities()
        goals = create_sample_business_goals()
        create_sample_recommendations(goals, capabilities)
        
        print("\n" + "=" * 50)
        print("✅ Test data creation completed successfully!")
        print("=" * 50)
        print(f"Created:")
        print(f"  - {Capability.objects.count()} Capabilities")
        print(f"  - {BusinessGoal.objects.count()} Business Goals")
        print(f"  - {CapabilityRecommendation.objects.count()} Recommendations")
        print("\nYou can now:")
        print("  1. Access Django Admin at: http://localhost:8000/admin/")
        print("  2. Test the API endpoints")
        print("  3. Run the development server: python manage.py runserver")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 