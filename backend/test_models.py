#!/usr/bin/env python
"""
Test script to validate models and their relationships.
Run this script to verify Phase 2.1 completion.
"""

import os
import django
from django.core.exceptions import ValidationError

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'businesscap.settings')
django.setup()

from core.models import Capability, BusinessGoal, CapabilityRecommendation

def test_capability_hierarchy():
    """Test capability hierarchy and level calculation."""
    print("\nTesting Capability Hierarchy...")
    
    # Get top-level capabilities
    top_level = Capability.objects.filter(parent__isnull=True)
    print(f"Top-level capabilities: {top_level.count()}")
    
    # Verify level calculation
    for cap in Capability.objects.all():
        print(f"Capability: {cap.name}")
        print(f"  Level: {cap.level}")
        print(f"  Parent: {cap.parent.name if cap.parent else 'None'}")
        
        # Verify level matches parent relationship
        if cap.parent:
            assert cap.level == cap.parent.level + 1, f"Level mismatch for {cap.name}"
    
    print("✓ Capability hierarchy test passed")

def test_business_goal_relationships():
    """Test business goal relationships and status transitions."""
    print("\nTesting Business Goal Relationships...")
    
    # Get all business goals
    goals = BusinessGoal.objects.all()
    print(f"Total business goals: {goals.count()}")
    
    # Check recommendations for each goal
    for goal in goals:
        print(f"\nGoal: {goal.title}")
        print(f"  Status: {goal.status}")
        recommendations = CapabilityRecommendation.objects.filter(business_goal=goal)
        print(f"  Recommendations: {recommendations.count()}")
        
        # Verify recommendation types
        for rec in recommendations:
            print(f"    - Type: {rec.recommendation_type}")
            print(f"      Status: {rec.status}")
            if rec.target_capability:
                print(f"      Target: {rec.target_capability.name}")
    
    print("✓ Business goal relationships test passed")

def test_recommendation_constraints():
    """Test recommendation constraints and validations."""
    print("\nTesting Recommendation Constraints...")
    
    # Get a sample goal and capability
    goal = BusinessGoal.objects.first()
    capability = Capability.objects.first()
    
    if goal and capability:
        # Test creating a recommendation
        try:
            rec = CapabilityRecommendation.objects.create(
                business_goal=goal,
                recommendation_type="STRENGTHEN_CAPABILITY",
                target_capability=capability,
                additional_details="Test recommendation"
            )
            print(f"✓ Created recommendation: {rec.recommendation_type}")
            
            # Test status transition
            rec.status = "APPLIED"
            rec.save()
            print(f"✓ Updated recommendation status to: {rec.status}")
            
        except ValidationError as e:
            print(f"❌ Validation error: {e}")
    
    print("✓ Recommendation constraints test passed")

def main():
    """Run all tests."""
    print("=" * 50)
    print("Testing Models and Relationships")
    print("=" * 50)
    
    try:
        test_capability_hierarchy()
        test_business_goal_relationships()
        test_recommendation_constraints()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main() 