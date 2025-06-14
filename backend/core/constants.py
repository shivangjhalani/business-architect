# Content Type Constants and Mappings since models use uppercase constants and api uses shake_case

# Backend model content types (used in database)
class ContentTypes:
    CAPABILITY = 'CAPABILITY'
    BUSINESS_GOAL = 'BUSINESS_GOAL'
    RECOMMENDATION = 'RECOMMENDATION'

# API endpoint content types (used in URLs)
API_CONTENT_TYPES = {
    'capabilities': 'capabilities',
    'business-goals': 'business-goals',
    'recommendations': 'recommendations'
}

# Mapping from API content types to model content types
API_TO_MODEL_CONTENT_TYPE = {
    'capabilities': ContentTypes.CAPABILITY,
    'business-goals': ContentTypes.BUSINESS_GOAL,
    'recommendations': ContentTypes.RECOMMENDATION
}

# Reverse mapping from model content types to API content types
MODEL_TO_API_CONTENT_TYPE = {v: k for k, v in API_TO_MODEL_CONTENT_TYPE.items()}

# Valid API content types for validation
VALID_API_CONTENT_TYPES = list(API_TO_MODEL_CONTENT_TYPE.keys())

# Valid model content types for validation
VALID_MODEL_CONTENT_TYPES = [ContentTypes.CAPABILITY, ContentTypes.BUSINESS_GOAL, ContentTypes.RECOMMENDATION] 