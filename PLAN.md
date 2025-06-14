## Project: AI-Powered Business Capability Map Management System

**Goal:** Develop a minimal, yet robust, AI-powered application to manage, analyze, and evolve an organization's business capability map. The application will leverage the Gemini API for intelligent insights and recommendations, enhanced with FAISS vector database for semantic search and improved context retrieval, with a Django backend for business logic and data persistence, and a React frontend for an intuitive user experience.

### Development Environment & Setup

**Environment Setup:**
* The project uses Nix for development environment management via `shell.nix`
* Key dependencies managed through Nix:
  * Python 3.11+ for Django backend
  * Node.js 18+ for React frontend
  * PostgreSQL for database
  * FAISS for vector similarity search
  * Development tools (git, curl, etc.)

**Python Virtual Environment:**
* Create and use a virtual environment in the backend directory:
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate  # On Unix/macOS
  # or
  .\venv\Scripts\activate  # On Windows
  ```

**Vector Database Setup:**
* FAISS (Facebook AI Similarity Search) will be used for semantic search capabilities:
  ```bash
  # Install FAISS in the virtual environment
  pip install faiss-cpu
  # For GPU support (optional): pip install faiss-gpu
  
  # Initialize vector storage directory
  mkdir -p backend/vector_storage
  ```

**PostgreSQL Setup:**
* Initialize and manage PostgreSQL database:
  ```
  # First, ensure you're in the Nix shell environment
  nix-shell  # This will load the Nix shell environment

  # Create data directory if not present
  mkdir -p pgdata

  # Initialize PostgreSQL database
  initdb -D pgdata

  # Start PostgreSQL server
  pg_ctl -D pgdata -l pgdata/postgres.log start

  # Create the database
  createdb business_cap

  # To stop PostgreSQL server when done
  pg_ctl -D pgdata stop
  ```


**UI Framework:**
* Frontend uses Shadcn UI components for a consistent, modern look
* Tailwind CSS for styling
* Key Shadcn components to be used:
  * Layout components (Card, Dialog, AlertDialog)
  * Form components (Input, Textarea, Select)
  * Data display (Table, Tree)
  * Navigation (Tabs, Breadcrumb)
  * Feedback (Toast, Progress)

---

### 1. Core Concepts & Data Model (Backend - Django Models & PostgreSQL Schema)

The application revolves around two primary entities: **Business Capabilities** and **Business Goals**.

**1.1. Business Capability Model:**
* **`Capability` (Django Model):** Represents a distinct business ability.
    * `id` (UUIDField or AutoField - Primary Key)
    * `name` (CharField): e.g., "Customer Relationship Management", "Product Innovation"
    * `description` (TextField): Detailed explanation of the capability.
    * `parent` (ForeignKey to self, null=True, blank=True): Establishes the hierarchy (e.g., "Customer Relationship Management" could be a parent of "Customer Onboarding").
    * `level` (PositiveIntegerField): Denotes the hierarchy level (e.g., 1 for top-level, 2 for sub-capability). This can be auto-calculated on save.
    * `status` (CharField, choices=['CURRENT', 'PROPOSED', 'DEPRECATED', 'ARCHIVED']): Current state of the capability.
    * `strategic_importance` (CharField, choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']): How vital the capability is to the business strategy.
    * `owner` (CharField, null=True, blank=True): The business unit or individual responsible for this capability.
    * `notes` (TextField, null=True, blank=True): Any additional internal notes.
    * `created_at` (DateTimeField, auto_now_add=True)
    * `updated_at` (DateTimeField, auto_now=True)

**1.2. Business Goal Model:**
* **`BusinessGoal` (Django Model):** Represents a strategic objective submitted by the user.
    * `id` (UUIDField or AutoField - Primary Key)
    * `title` (CharField): Brief title of the goal.
    * `description` (TextField): Detailed explanation of the business goal (free-form text input).
    * `pdf_file` (FileField, upload_to='business_goals/pdfs/', null=True, blank=True): Optional PDF document containing goal details.
    * `status` (CharField, choices=['PENDING_ANALYSIS', 'ANALYZED', 'RECOMMENDATIONS_APPLIED', 'CLOSED']): Lifecycle of the goal analysis.
    * `submitted_at` (DateTimeField, auto_now_add=True)

**1.3. Capability Recommendation Model:**
* **`CapabilityRecommendation` (Django Model):** Stores AI-generated recommendations for map changes.
    * `id` (UUIDField or AutoField - Primary Key)
    * `business_goal` (ForeignKey to `BusinessGoal`): The goal that triggered this recommendation.
    * `recommendation_type` (CharField, choices=['ADD_CAPABILITY', 'MODIFY_CAPABILITY', 'DELETE_CAPABILITY', 'STRENGTHEN_CAPABILITY', 'MERGE_CAPABILITIES', 'SPLIT_CAPABILITY']): Type of recommended action.
    * `target_capability` (ForeignKey to `Capability`, null=True, blank=True): The existing capability being targeted (for modify, delete, strengthen).
    * `proposed_name` (CharField, null=True, blank=True): New name if adding/modifying.
    * `proposed_description` (TextField, null=True, blank=True): New description if adding/modifying.
    * `proposed_parent` (ForeignKey to `Capability`, null=True, blank=True): New parent if moving/adding.
    * `additional_details` (TextField, null=True, blank=True): LLM's explanation for the recommendation.
    * `status` (CharField, choices=['PENDING', 'APPLIED', 'REJECTED']): User's action on the recommendation.
    * `recommended_by_ai_at` (DateTimeField, auto_now_add=True)
    * `applied_at` (DateTimeField, null=True, blank=True)

**1.4. Vector Database Models & Integration (FAISS):**

* **`VectorEmbedding` (Django Model):** Stores metadata for vector embeddings.
    * `id` (UUIDField - Primary Key)
    * `content_type` (CharField, choices=['CAPABILITY', 'BUSINESS_GOAL', 'RECOMMENDATION']): Type of content embedded.
    * `object_id` (UUIDField): Foreign key to the related object.
    * `embedding_model` (CharField, default='text-embedding-004'): Model used to generate embeddings.
    * `vector_index` (IntegerField): Index position in FAISS vector store.
    * `created_at` (DateTimeField, auto_now_add=True)
    * `updated_at` (DateTimeField, auto_now=True)

* **FAISS Vector Storage Structure:**
    * **Capability Vectors:** Store embeddings of capability names + descriptions for semantic similarity search.
    * **Business Goal Vectors:** Store embeddings of goal titles + descriptions for finding similar past goals.
    * **Recommendation Vectors:** Store embeddings of recommendation details for pattern matching and reuse.
    * **Vector Files:** Stored in `backend/vector_storage/` directory:
        * `capabilities.faiss` - FAISS index for capabilities
        * `business_goals.faiss` - FAISS index for business goals  
        * `recommendations.faiss` - FAISS index for recommendations

* **Vector Service Layer:**
    * **`VectorManager` (Python Class):** Handles all FAISS operations.
        * `generate_embedding(text)` - Generate embeddings using Gemini
        * `add_vector(embedding, metadata)` - Add new vector to FAISS index
        * `search_similar(query_embedding, k=5)` - Find k most similar vectors
        * `update_vector(index, embedding)` - Update existing vector
        * `delete_vector(index)` - Remove vector from index
        * `save_index()` - Persist FAISS index to disk
        * `load_index()` - Load FAISS index from disk

---

### 2. Backend Implementation (Django & PostgreSQL)

**2.1. API Endpoints (Django REST Framework):**

* **`api/capabilities/`:**
    * `GET`: List all capabilities (with optional filtering by `level`, `status`, `parent`). Serialize with nested representation for parent/children relationships.
    * `POST`: Create a new capability.
* **`api/capabilities/<uuid:id>/`:**
    * `GET`: Retrieve a single capability.
    * `PUT`/`PATCH`: Update an existing capability.
    * `DELETE`: Delete a capability (handle cascading or disassociating children).
* **`api/capabilities/<uuid:id>/similar/`:**
    * `GET`: Find similar capabilities using vector search. Query parameters: `limit` (default 5), `threshold` (similarity threshold).
* **`api/capabilities/search/`:**
    * `POST`: Semantic search across capabilities. Request body: `{"query": "text", "limit": 10}`.
* **`api/business-goals/`:**
    * `GET`: List all business goals.
    * `POST`: Submit a new business goal. Allow `multipart/form-data` for optional PDF upload.
* **`api/business-goals/<uuid:id>/analyze/`:**
    * `POST`: Trigger the AI analysis for a specific business goal. This endpoint should be asynchronous, initiating a background task (e.g., using Celery, though for "minimal" we can initially just run it synchronously or use Django's `threading` for a simpler background worker if it's not too long-running).
* **`api/business-goals/<uuid:id>/similar/`:**
    * `GET`: Find similar business goals using vector search to provide context for analysis.
* **`api/business-goals/<uuid:id>/recommendations/`:**
    * `GET`: Retrieve all `CapabilityRecommendation` objects associated with a specific business goal.
* **`api/business-goals/search/`:**
    * `POST`: Semantic search across business goals. Request body: `{"query": "text", "limit": 10}`.
* **`api/recommendations/<uuid:id>/apply/`:**
    * `POST`: Apply a specific `CapabilityRecommendation` to update the `Capability` map. This involves creating, modifying, or deleting `Capability` records based on the recommendation type.
* **`api/recommendations/<uuid:id>/similar/`:**
    * `GET`: Find similar past recommendations to validate or suggest improvements.
* **`api/recommendations/search/`:**
    * `POST`: Semantic search across recommendations. Request body: `{"query": "text", "limit": 10}`.
* **`api/llm/query/`:**
    * `POST`: AI assistant endpoint with automatic vector context enhancement.
        * **Request Body:** `{"query": "string", "context": "string (optional, e.g., current capability map snapshot)"}`
        * **Response Body:** `{"answer": "string", "query": "string", "context_used": "string", "vector_context": {"similar_capabilities": [...], "similar_goals": [...], "similar_recommendations": [...], "context_enhancement": "string"}}`
        * **Vector Enhancement:** Automatically searches for similar capabilities, goals, and recommendations to enhance AI responses with relevant context.
* **`api/vectors/rebuild/`:**
    * `POST`: Rebuild all FAISS indexes (admin operation). Useful after bulk data changes.
* **`api/vectors/status/`:**
    * `GET`: Get status of vector indexes (count, last updated, etc.).

**2.2. LLM Integration Logic (Gemini API - Python Client):**

* **Configuration:**
    * Store `GEMINI_API_KEY` securely in Django settings or environment variables.
    * Initialize the Gemini client.
    * Configure FAISS vector manager for embedding generation and similarity search.
* **A. Interactive Business Q&A (`api/llm/query/`):**
    * Receive user `query`.
    * **Vector-Enhanced Context Retrieval:**
        * Generate embedding for the user query using Gemini embedding API.
        * Search for similar capabilities, goals, and recommendations using FAISS.
        * Retrieve top 3-5 most relevant items from each category.
    * **Prompt Engineering:** Construct a prompt that includes:
        * System instructions: "You are a business architect AI. Answer questions about business capabilities and strategy concisely."
        * Context: Dynamically fetch and include a summary of the current business capability map (e.g., top-level capabilities and their descriptions) from the database to provide context to the LLM.
        * **Enhanced Context from Vector Search:** Include similar capabilities, past goals, and recommendations found via vector search.
        * User query.
    * Call `gemini_pro.generate_content()` with the constructed prompt.
    * Return the LLM's generated `text`.
* **B. Goal-Driven Analysis (`api/business-goals/<id>/analyze/`):**
    * **PDF Processing:** If `business_goal.pdf_file` exists:
        * Use `PyPDF2` or `pdfplumber` to extract text content from the PDF.
        * Concatenate PDF text with `business_goal.description`.
    * **Vector-Enhanced Context Retrieval:**
        * Generate embedding for the business goal description.
        * Find similar past business goals using FAISS vector search.
        * Retrieve their successful recommendations and outcomes.
        * Find related capabilities that might be impacted.
    * **Prompt Engineering:** This is critical.
        * **Instruction:** "You are a highly skilled business architect AI. Analyze the provided business goal in the context of the current business capabilities and similar past goals. Recommend changes to the capability map (add, modify, delete, strengthen, merge, split) to achieve this goal. Provide recommendations in a structured JSON format."
        * **Current Capability Map Context:** Include the *entire* current capability map (serialized to JSON) for the LLM to understand the existing landscape.
        * **Similar Goals Context:** Include 3-5 most similar past business goals and their successful recommendations.
        * **Related Capabilities:** Include capabilities that are semantically similar to the goal.
        * **Business Goal:** Provide the extracted text from the `BusinessGoal` object.
        * **Desired JSON Output Format (Crucial for parsing!):**
            ```json
            {
              "summary_of_impact": "Overall summary of how goals impact capabilities.",
              "similar_goals_insights": "Key insights from analyzing similar past goals.",
              "recommendations": [
                {
                  "type": "ADD_CAPABILITY", // or MODIFY_CAPABILITY, DELETE_CAPABILITY, etc.
                  "rationale": "Explanation for this recommendation.",
                  "confidence_score": 0.85, // 0-1 confidence based on similar past successes
                  "details": {
                    // For ADD_CAPABILITY:
                    "proposed_name": "New Capability Name",
                    "proposed_description": "Description...",
                    "proposed_parent_name": "Existing Parent Capability Name (or null for top-level)"
                  }
                }
                // ... other types with confidence scores
              ]
            }
            ```
    * **LLM Call:** Call `gemini_pro.generate_content()` with the detailed prompt.
    * **Response Parsing:**
        * Attempt to parse the LLM's `text` response as JSON. Implement robust error handling for malformed JSON.
        * Iterate through the `recommendations` array from the parsed JSON.
        * For each recommendation, create a new `CapabilityRecommendation` object in the database.
        * **Vector Storage:** Generate and store embeddings for new recommendations in FAISS.
        * **Crucial:** When the LLM references existing capabilities by *name*, retrieve their `id` from the database to correctly link `target_capability` foreign keys. If a name doesn't match an existing capability, flag it or handle it as an error.
    * Update `BusinessGoal.status` to `ANALYZED`.

**2.3. Vector Database Integration (FAISS Implementation):**

* **Vector Manager Service (`core/services/vector_manager.py`):**
    * **Initialization:**
        * Load existing FAISS indexes on startup or create new ones.
        * Initialize embedding model (Gemini embedding API).
        * Set up index mappings and metadata storage.
    * **Embedding Generation:**
        * `generate_embedding(text)`: Use Gemini embedding API to create 768-dimensional vectors.
        * Handle text preprocessing (cleaning, truncation to token limits).
        * Implement caching for frequently embedded content.
    * **FAISS Operations:**
        * `add_to_index(content_type, object_id, text)`: Generate embedding and add to appropriate FAISS index.
        * `search_similar(content_type, query_text, k=5, threshold=0.7)`: Find similar items with similarity scores.
        * `update_embedding(content_type, object_id, new_text)`: Update existing vector.
        * `remove_from_index(content_type, object_id)`: Remove vector when object is deleted.
    * **Index Management:**
        * Separate FAISS indexes for capabilities, business goals, and recommendations.
        * Periodic index optimization and cleanup.
        * Backup and restore functionality.

* **Model Signal Handlers:**
    * **Auto-Embedding:** Automatically generate and store embeddings when objects are created/updated:
        * `Capability` save signal → generate embedding from name + description
        * `BusinessGoal` save signal → generate embedding from title + description
        * `CapabilityRecommendation` save signal → generate embedding from recommendation details
    * **Auto-Cleanup:** Remove embeddings when objects are deleted.

* **Vector Search API Views:**
    * Implement semantic search endpoints for each content type.
    * Return results with similarity scores and relevance ranking.
    * Support filtering and pagination for search results.

**2.4. Capability Map Update Logic (`api/recommendations/<id>/apply/`):**

* When a user "applies" a recommendation:
    * Retrieve the `CapabilityRecommendation` object.
    * Based on `recommendation_type`:
        * **ADD_CAPABILITY:** Create a new `Capability` instance with `status='CURRENT'`.
        * **MODIFY_CAPABILITY:** Find `target_capability` and update its fields (name, description, parent).
        * **DELETE_CAPABILITY:** Find `target_capability` and set its `status` to `DEPRECATED` or `ARCHIVED` (soft delete). Handle children: re-parent to the deleted capability's parent or mark them similarly.
        * **STRENGTHEN_CAPABILITY:** Update `target_capability`'s `strategic_importance` or add a note indicating focus.
        * **MERGE_CAPABILITIES:** Identify two capabilities to merge, create a new one, move children/associations, and deprecate the original two. (Complex, potentially beyond "minimal" for V1).
        * **SPLIT_CAPABILITY:** Identify one capability, create new ones, and deprecate the original. (Complex, potentially beyond "minimal" for V1).
    * Set `CapabilityRecommendation.status` to `APPLIED` and `applied_at` timestamp.
    * **Update Vector Indexes:** When capabilities are modified/added/deleted, update corresponding FAISS embeddings.
    * Implement database transactions for atomicity for complex operations.

---

### 3. Frontend Implementation (React & Shadcn UI)

**3.1. Main Layout & Navigation:**

* **`App.js` / `Layout.js`:**
    * Utilize Shadcn `Layout` or similar structure for consistent header, sidebar, and main content area.
    * **Header:** App title, possibly user profile/settings (minimal for now).
    * **Sidebar Navigation:**
        * "Business Capability Map" (view/edit capabilities)
        * "Submit Business Goals"
        * "Analyze Goals & Recommendations"
        * "Semantic Search" (vector-powered search across all content)
        * "Ask AI" (general Q&A)

**3.2. Key Components & Pages:**

* **A. `CapabilityMapViewer.jsx` (Business Capability Map Page):**
    * **Visualization:** Display capabilities in a hierarchical, tree-like structure. Shadcn `Tree` or custom nested `Card` components.
    * Each capability node should be clickable to view/edit details.
    * **Enhanced Search Features:**
        * **Semantic Search Bar:** Input field that uses vector search to find capabilities by meaning, not just keywords.
        * **"Find Similar" Button:** For each capability, show similar capabilities using vector search.
        * **Duplicate Detection:** Highlight potentially duplicate capabilities found via similarity search.
    * **CRUD Operations:**
        * **Add Capability:** Button to open a Shadcn `Dialog` with a `Form` for new capability details (name, description, parent dropdown, importance, status).
        * **Edit Capability:** Clicking a capability opens a `Dialog` with its details pre-filled for editing.
        * **Delete Capability:** Button within the edit dialog or on the node itself, with a confirmation `AlertDialog`.
    * **Filtering/Search:** Input fields to filter capabilities by name, status, importance, plus semantic search.
* **B. `GoalSubmissionForm.jsx` (Submit Business Goals Page):**
    * Shadcn `Form` component.
    * **Fields:**
        * `title` (Input)
        * `description` (Textarea)
        * `pdf_file` (Input type="file")
    * **Smart Suggestions:** As user types description, show similar past goals using vector search.
    * **Submission Button:** Triggers `POST` request to `api/business-goals/`.
    * Loading state indication.
* **C. `GoalAnalysisAndRecommendations.jsx` (Analyze Goals & Recommendations Page):**
    * **List Goals:** Display a `Table` of all submitted `BusinessGoal`s, showing `title`, `submitted_at`, and `status`.
    * **"Analyze" Button:** For goals with `PENDING_ANALYSIS` status, a button to trigger `POST` to `api/business-goals/<id>/analyze/`. Show loading state.
    * **Similar Goals Section:** For each goal, show similar past goals with their outcomes.
    * **View Recommendations:** For `ANALYZED` goals, a button to navigate to `RecommendationList.jsx` or expand within the table.
    * **Recommendation List (within this component or separate `RecommendationList.jsx`):**
        * Display `CapabilityRecommendation`s as a list or `Card`s.
        * Each recommendation card should show: `recommendation_type`, `details` (parsed JSON), `rationale`, `status`, `confidence_score`.
        * **Similar Recommendations:** Show similar past recommendations and their success rates.
        * **Action Buttons:** For `PENDING` recommendations:
            * `Apply` Button (Shadcn `Button`): Triggers `POST` to `api/recommendations/<id>/apply/`. Show loading state.
            * `Reject` Button (Shadcn `Button`): Updates `CapabilityRecommendation.status` to `REJECTED` via `PATCH` request.
* **D. `SemanticSearchPage.jsx` (New Vector Search Page):**
    * **Universal Search Interface:**
        * Single search input that searches across capabilities, goals, and recommendations.
        * Tabbed results showing different content types.
        * Similarity scores and relevance indicators.
    * **Advanced Search Options:**
        * Filter by content type (capabilities, goals, recommendations).
        * Adjust similarity threshold.
        * Date range filters.
    * **Search Results:**
        * Highlighted matching text.
        * Links to original items.
        * Contextual information and similarity explanations.
* **E. `LLMQueryInterface.jsx` (Ask AI Page):**
    * **Enhanced Chat-like Interface:**
        * Input field (Shadcn `Input` or `Textarea`) for user queries.
        * Send button.
        * Display area for previous queries and AI responses (e.g., using `Card` components for chat bubbles).
        * **Context Indicators:** Show when AI is using vector search results to enhance answers.
    * **Smart Context:** Automatically include relevant similar content from vector search.
    * Loading indicator when AI is thinking.
    * Calls `POST` to `api/llm/query/`.

**3.3. Enhanced UI Components:**

* **`SimilarityIndicator.jsx`:** Component to show similarity scores and relevance.
* **`VectorSearchInput.jsx`:** Reusable semantic search input component.
* **`RecommendationConfidence.jsx`:** Display confidence scores for recommendations.
* **`ContextualResults.jsx`:** Show related items found via vector search.

**3.4. State Management:**

* For a minimal application, React Context API or a lightweight library like Zustand or Jotai is recommended for global state (e.g., currently loaded capabilities, user authentication if added later, loading states).

**3.5. API Interaction:**

* Use `fetch` API or `axios` for all backend API calls.
* Handle loading states and error states for all API interactions.

---

### 4. General Implementation Details

* **Error Handling:** Implement robust error handling on both backend and frontend. Display user-friendly error messages.
* **Validation:** Backend validation (Django models, serializers) and frontend validation (React forms).
* **Authentication/Authorization (Future Consideration, Minimal for V1):** For a production app, you'd need user authentication. For initial "minimal" build, can be omitted or assume a single user.
* **Styling:** Consistently use Shadcn UI components and Tailwind CSS utilities for a clean and consistent look.
* **Documentation:** Basic READMEs for frontend and backend, explaining setup and running instructions.
* **Testing (Minimal):** Basic unit tests for critical backend logic (e.g., PDF parsing, recommendation application).
* **Deployment (Optional initial thought):** Containerize Django and React apps using Docker for easier deployment.

---

## 5. Complete API Documentation

### **5.1. Base Configuration**

* **Base URL:** `http://localhost:8000/api/`
* **Documentation:** `http://localhost:8000/swagger/` (Swagger UI)
* **Authentication:** AllowAny (development) - No authentication required for V1
* **Content-Type:** `application/json` for most endpoints, `multipart/form-data` for file uploads
* **Pagination:** 20 items per page by default

### **5.2. Capabilities Management API**

#### **GET /api/capabilities/**
List all business capabilities with filtering and search support.

**Query Parameters:**
- `status` - Filter by status (CURRENT, PROPOSED, DEPRECATED, ARCHIVED)
- `level` - Filter by hierarchy level (1, 2, 3, etc.)
- `parent` - Filter by parent capability ID
- `strategic_importance` - Filter by importance (CRITICAL, HIGH, MEDIUM, LOW)
- `search` - Search in name, description, owner fields
- `ordering` - Order by fields (name, level, created_at, strategic_importance)
- `root_only=true` - Get only root-level capabilities
- `parent_id={uuid}` - Get children of specific capability
- `max_level={number}` - Filter capabilities up to specific level

**Example Request:**
```bash
# Basic list
curl -X GET "http://localhost:8000/api/capabilities/"

# With filters
curl -X GET "http://localhost:8000/api/capabilities/?status=CURRENT&level=1&ordering=name"

# Search capabilities
curl -X GET "http://localhost:8000/api/capabilities/?search=customer&strategic_importance=CRITICAL"

# Get root capabilities only
curl -X GET "http://localhost:8000/api/capabilities/?root_only=true"
```

**Example Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-here",
      "name": "Customer Relationship Management",
      "description": "Comprehensive management of customer interactions...",
      "parent": null,
      "parent_name": null,
      "level": 1,
      "status": "CURRENT",
      "strategic_importance": "CRITICAL",
      "owner": "Sales & Marketing",
      "notes": null,
      "created_at": "2025-06-04T16:50:12.971397Z",
      "updated_at": "2025-06-04T16:50:12.971424Z",
      "children_count": 3,
      "full_path": "Customer Relationship Management"
    }
  ]
}
```

#### **POST /api/capabilities/**
Create a new business capability.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/capabilities/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Digital Marketing Automation",
    "description": "Automated marketing workflows and customer journey management",
    "parent": "parent-capability-uuid",
    "status": "PROPOSED",
    "strategic_importance": "HIGH",
    "owner": "Marketing Team",
    "notes": "Implementation planned for Q3"
  }'
```

**Response:** `201 Created` with capability object

#### **GET /api/capabilities/{id}/**
Retrieve a single capability with nested children.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/"
```

**Example Response:**
```json
{
  "id": "uuid-here",
  "name": "Customer Relationship Management",
  "description": "Comprehensive management of customer interactions...",
  "parent": null,
  "parent_name": null,
  "level": 1,
  "status": "CURRENT",
  "strategic_importance": "CRITICAL",
  "owner": "Sales & Marketing",
  "notes": null,
  "created_at": "2025-06-04T16:50:12.971397Z",
  "updated_at": "2025-06-04T16:50:12.971424Z",
  "children": [
    {
      "id": "child-uuid",
      "name": "Customer Acquisition",
      "level": 2,
      "children_count": 2
    }
  ],
  "full_path": "Customer Relationship Management",
  "ancestor_count": 0,
  "descendant_count": 5
}
```

#### **PUT/PATCH /api/capabilities/{id}/**
Update an existing capability.

**Example Request:**
```bash
# Partial update (PATCH)
curl -X PATCH "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategic_importance": "CRITICAL",
    "owner": "New Owner Team"
  }'

# Full update (PUT)
curl -X PUT "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Relationship Management",
    "description": "Updated description...",
    "strategic_importance": "CRITICAL",
    "status": "CURRENT",
    "owner": "Sales & Marketing Team"
  }'
```

#### **DELETE /api/capabilities/{id}/**
Soft delete a capability (sets status to ARCHIVED).

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/"
```

**Response:** `204 No Content`

**Error Response (if has children):**
```json
{
  "error": true,
  "message": "Cannot delete capability with children. Please reassign or delete children first.",
  "status_code": 400
}
```

#### **GET /api/capabilities/{id}/children/**
Get direct children of a capability.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/children/"
```

#### **GET /api/capabilities/{id}/ancestors/**
Get all ancestor capabilities in the hierarchy.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/capabilities/151fb03c-099b-40b8-9dbd-29a0d161099c/ancestors/"
```

#### **GET /api/capabilities/{id}/descendants/**
Get all descendant capabilities.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/descendants/"
```

#### **GET /api/capabilities/{id}/similar/**
Find similar capabilities using vector search.

**Query Parameters:**
- `limit` - Number of similar capabilities to return (default: 5, max: 20)
- `threshold` - Similarity threshold (0.0-1.0, default: 0.7)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/capabilities/68b89725-0334-4b4d-aa58-67007878c3bb/similar/?limit=3&threshold=0.8"
```

**Example Response:**
```json
{
  "similar_capabilities": [
    {
      "id": "similar-uuid-1",
      "name": "Customer Service Management",
      "description": "Managing customer support and service delivery...",
      "similarity_score": 0.89,
      "full_path": "Customer Operations > Customer Service Management"
    },
    {
      "id": "similar-uuid-2", 
      "name": "Customer Experience Design",
      "description": "Designing and optimizing customer experience journeys...",
      "similarity_score": 0.83,
      "full_path": "Customer Operations > Customer Experience Design"
    }
  ],
  "query_capability": {
    "id": "68b89725-0334-4b4d-aa58-67007878c3bb",
    "name": "Customer Relationship Management"
  }
}
```

#### **POST /api/capabilities/search/**
Semantic search across all capabilities using vector similarity.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/capabilities/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "customer satisfaction and retention strategies",
    "limit": 10,
    "threshold": 0.6
  }'
```

**Example Response:**
```json
{
  "results": [
    {
      "id": "uuid-1",
      "name": "Customer Retention Programs",
      "description": "Development and management of customer loyalty programs...",
      "similarity_score": 0.92,
      "full_path": "Customer Operations > Customer Retention Programs",
      "strategic_importance": "HIGH"
    }
  ],
  "query": "customer satisfaction and retention strategies",
  "total_results": 5,
  "search_time_ms": 45
}
```

### **5.3. Business Goals Management API**

#### **GET /api/business-goals/**
List all business goals with filtering.

**Query Parameters:**
- `status` - Filter by status (PENDING_ANALYSIS, ANALYZED, RECOMMENDATIONS_APPLIED, CLOSED)
- `search` - Search in title, description
- `ordering` - Order by submitted_at, title

**Example Request:**
```bash
# Basic list
curl -X GET "http://localhost:8000/api/business-goals/"

# With filters
curl -X GET "http://localhost:8000/api/business-goals/?status=PENDING_ANALYSIS&ordering=-submitted_at"

# Search goals
curl -X GET "http://localhost:8000/api/business-goals/?search=digital transformation"
```

**Example Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-here",
      "title": "Digital Transformation of Sales Process",
      "description": "Modernize our sales process through digital tools...",
      "pdf_file": null,
      "status": "ANALYZED",
      "submitted_at": "2025-06-04T16:50:13.017866Z",
      "recommendations_count": 3,
      "pending_recommendations_count": 2,
      "is_analyzed": true,
      "pdf_filename": null
    }
  ]
}
```

#### **POST /api/business-goals/**
Submit a new business goal for analysis.

**Content-Type:** `multipart/form-data` (for file upload)

**Example Request:**
```bash
# Text only
curl -X POST "http://localhost:8000/api/business-goals/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Improve Customer Retention",
    "description": "Increase customer retention from 75% to 90% within 12 months through improved service and loyalty programs."
  }'

# With PDF file
curl -X POST "http://localhost:8000/api/business-goals/" \
  -F "title=Improve Customer Retention" \
  -F "description=Increase customer retention from 75% to 90% within 12 months through improved service and loyalty programs." \
  -F "pdf_file=@/path/to/business-plan.pdf"
```

**Response:** `201 Created` with goal object

#### **GET /api/business-goals/{id}/**
Retrieve a single business goal with recommendations.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/business-goals/0bdb7723-d885-4fc3-9f77-14cefab997d9/"
```

**Example Response:**
```json
{
  "id": "uuid-here",
  "title": "Digital Transformation of Sales Process",
  "description": "Modernize our sales process...",
  "pdf_file": null,
  "status": "ANALYZED",
  "submitted_at": "2025-06-04T16:50:13.017866Z",
  "recommendations_count": 3,
  "pending_recommendations_count": 2,
  "is_analyzed": true,
  "pdf_filename": null,
  "recommendations": [
    {
      "id": "rec-uuid",
      "recommendation_type": "ADD_CAPABILITY",
      "proposed_name": "Digital Sales Tools",
      "status": "PENDING"
    }
  ]
}
```

#### **POST /api/business-goals/{id}/analyze/**
Trigger AI analysis for a business goal.

**Prerequisites:** Goal must have status `PENDING_ANALYSIS`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/business-goals/e1a51d62-f5f7-4031-9503-ee77e8c9dd04/analyze/" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Example Response:**
```json
{
  "status": "analysis complete",
  "recommendations_created": 3,
  "summary": "Analysis identified opportunities to enhance CRM capabilities and add new digital sales tools to support the transformation objectives."
}
```

**Error Response:**
```json
{
  "error": true,
  "message": "Goal is already analyzed. Only pending goals can be analyzed.",
  "status_code": 400
}
```

#### **GET /api/business-goals/{id}/recommendations/**
Get all recommendations for a specific business goal.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/business-goals/0bdb7723-d885-4fc3-9f77-14cefab997d9/recommendations/"
```

#### **GET /api/business-goals/{id}/similar/**
Find similar business goals using vector search to provide analysis context.

**Query Parameters:**
- `limit` - Number of similar goals to return (default: 5, max: 10)
- `threshold` - Similarity threshold (0.0-1.0, default: 0.7)
- `include_outcomes` - Include recommendation outcomes (default: true)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/business-goals/0bdb7723-d885-4fc3-9f77-14cefab997d9/similar/?limit=3&include_outcomes=true"
```

**Example Response:**
```json
{
  "similar_goals": [
    {
      "id": "similar-goal-uuid-1",
      "title": "Modernize Customer Service Operations",
      "description": "Transform customer service through digital channels...",
      "similarity_score": 0.91,
      "status": "RECOMMENDATIONS_APPLIED",
      "successful_recommendations": 4,
      "submitted_at": "2024-01-15T10:30:00Z",
      "outcomes": {
        "capabilities_added": 2,
        "capabilities_modified": 1,
        "success_rate": 0.89
      }
    }
  ],
  "query_goal": {
    "id": "0bdb7723-d885-4fc3-9f77-14cefab997d9",
    "title": "Digital Transformation of Sales Process"
  }
}
```

#### **POST /api/business-goals/search/**
Semantic search across business goals.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/business-goals/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "digital transformation and automation",
    "limit": 8,
    "threshold": 0.65,
    "status_filter": ["ANALYZED", "RECOMMENDATIONS_APPLIED"]
  }'
```

**Example Response:**
```json
{
  "results": [
    {
      "id": "uuid-1",
      "title": "Automate Financial Reporting Process",
      "description": "Implement automated reporting systems to reduce manual work...",
      "similarity_score": 0.87,
      "status": "ANALYZED",
      "recommendations_count": 3,
      "submitted_at": "2024-02-01T14:20:00Z"
    }
  ],
  "query": "digital transformation and automation",
  "total_results": 4,
  "search_time_ms": 52
}
```

### **5.4. Recommendations Management API**

#### **GET /api/recommendations/**
List all capability recommendations.

**Query Parameters:**
- `recommendation_type` - Filter by type (ADD_CAPABILITY, MODIFY_CAPABILITY, DELETE_CAPABILITY, STRENGTHEN_CAPABILITY)
- `status` - Filter by status (PENDING, APPLIED, REJECTED)
- `business_goal` - Filter by business goal UUID
- `ordering` - Order by recommended_by_ai_at, status

**Example Request:**
```bash
# Basic list
curl -X GET "http://localhost:8000/api/recommendations/"

# Filter by status and type
curl -X GET "http://localhost:8000/api/recommendations/?status=PENDING&recommendation_type=ADD_CAPABILITY"

# Filter by business goal
curl -X GET "http://localhost:8000/api/recommendations/?business_goal=0bdb7723-d885-4fc3-9f77-14cefab997d9"

# Order by recent first
curl -X GET "http://localhost:8000/api/recommendations/?ordering=-recommended_by_ai_at"
```

**Example Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-here",
      "business_goal": "goal-uuid",
      "business_goal_title": "Digital Transformation of Sales Process",
      "recommendation_type": "ADD_CAPABILITY",
      "target_capability": null,
      "target_capability_details": null,
      "proposed_name": "Digital Sales Tools",
      "proposed_description": "Comprehensive digital toolset for modern sales processes...",
      "proposed_parent": "parent-uuid",
      "proposed_parent_details": {
        "id": "parent-uuid",
        "name": "Customer Relationship Management",
        "full_path": "Customer Relationship Management"
      },
      "additional_details": "New capability needed to support digital transformation objectives...",
      "status": "PENDING",
      "recommended_by_ai_at": "2025-06-04T16:50:13.025433Z",
      "applied_at": null,
      "is_actionable": true,
      "processing_duration": "214.606776"
    }
  ]
}
```

#### **POST /api/recommendations/{id}/apply/**
Apply a recommendation to update the capability map.

**Prerequisites:** Recommendation must have status `PENDING`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/recommendations/1b236e29-c9e0-49e0-9b82-0e6a14aa3d55/apply/" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Example Response:**
```json
{
  "status": "recommendation applied",
  "action_taken": "created_capability",
  "capability_id": "new-capability-uuid",
  "message": "Created new capability: Digital Sales Tools"
}
```

**Possible Actions:**
- `created_capability` - New capability created
- `modified_capability` - Existing capability updated
- `deprecated_capability` - Capability marked as deprecated
- `strengthened_capability` - Strategic importance increased

#### **POST /api/recommendations/{id}/reject/**
Mark a recommendation as rejected.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/recommendations/d52ee02d-0e97-4fb9-81f6-42ac892c2a7c/reject/" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "status": "recommendation rejected"
}
```

#### **GET /api/recommendations/{id}/similar/**
Find similar past recommendations for validation and improvement suggestions.

**Query Parameters:**
- `limit` - Number of similar recommendations to return (default: 5, max: 10)
- `threshold` - Similarity threshold (0.0-1.0, default: 0.75)
- `include_outcomes` - Include application outcomes (default: true)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/recommendations/1b236e29-c9e0-49e0-9b82-0e6a14aa3d55/similar/?limit=3&include_outcomes=true"
```

**Example Response:**
```json
{
  "similar_recommendations": [
    {
      "id": "similar-rec-uuid-1",
      "recommendation_type": "ADD_CAPABILITY",
      "proposed_name": "Digital Customer Portal",
      "similarity_score": 0.88,
      "status": "APPLIED",
      "business_goal_title": "Enhance Customer Self-Service",
      "applied_at": "2024-01-20T15:45:00Z",
      "outcome": {
        "success": true,
        "impact_rating": "HIGH",
        "implementation_notes": "Successfully improved customer satisfaction by 25%"
      }
    }
  ],
  "query_recommendation": {
    "id": "1b236e29-c9e0-49e0-9b82-0e6a14aa3d55",
    "recommendation_type": "ADD_CAPABILITY",
    "proposed_name": "Digital Sales Tools"
  },
  "success_patterns": {
    "similar_recommendations_success_rate": 0.85,
    "common_success_factors": ["Clear scope definition", "Stakeholder buy-in"]
  }
}
```

#### **POST /api/recommendations/search/**
Semantic search across capability recommendations.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/recommendations/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "automation and efficiency improvements",
    "limit": 8,
    "threshold": 0.7,
    "type_filter": ["ADD_CAPABILITY", "MODIFY_CAPABILITY"],
    "status_filter": ["APPLIED"]
  }'
```

**Example Response:**
```json
{
  "results": [
    {
      "id": "uuid-1",
      "recommendation_type": "ADD_CAPABILITY",
      "proposed_name": "Process Automation Engine",
      "proposed_description": "Automated workflow management system...",
      "similarity_score": 0.91,
      "status": "APPLIED",
      "business_goal_title": "Streamline Operations",
      "confidence_score": 0.89,
      "applied_at": "2024-01-15T10:30:00Z"
    }
  ],
  "query": "automation and efficiency improvements",
  "total_results": 6,
  "search_time_ms": 38
}
```

### **5.5. AI Assistant API**

#### **POST /api/llm/query/**
Query the AI assistant for business capability insights.

**Example Request:**
```bash
# Basic query
curl -X POST "http://localhost:8000/api/llm/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key capabilities for digital transformation?"
  }'

# Query with context
curl -X POST "http://localhost:8000/api/llm/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can we improve our customer retention rates?",
    "context": "Our current retention rate is 75% and we have strong CRM capabilities but weak customer service processes."
  }'

# Complex strategic question
curl -X POST "http://localhost:8000/api/llm/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What capabilities should we prioritize for AI implementation in our organization?"
  }'
```

**Example Response:**
```json
{
  "answer": "Based on your current capability map, key capabilities for digital transformation include:\n\n* **AI-Powered Analytics:** Drives data-driven decisions and automation.\n* **Customer Relationship Management:** Optimizes customer experience in the digital realm...",
  "query": "What are the key capabilities for digital transformation?",
  "context_used": "Current Business Capability Map Summary:\n• AI-Powered Analytics: Advanced analytics and machine learning capabilities...",
  "vector_context": {
    "similar_capabilities": [
      {
        "name": "Data Analytics Platform",
        "similarity_score": 0.89,
        "relevance": "Highly relevant for digital transformation analytics needs"
      }
    ],
    "similar_goals": [
      {
        "title": "Implement Data-Driven Decision Making",
        "similarity_score": 0.85,
        "outcome": "Successfully implemented analytics capabilities"
      }
    ],
    "context_enhancement": "Enhanced with 3 similar capabilities and 2 related past goals"
  }
}
```

### **5.6. Vector Database Management API**

#### **GET /api/vectors/status/**
Get the current status and health of all FAISS vector indexes.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/vectors/status/"
```

**Example Response:**
```json
{
  "indexes": {
    "capabilities": {
      "total_vectors": 245,
      "index_size_mb": 12.3,
      "last_updated": "2024-06-04T16:45:00Z",
      "health": "healthy"
    },
    "business_goals": {
      "total_vectors": 89,
      "index_size_mb": 4.7,
      "last_updated": "2024-06-04T15:30:00Z",
      "health": "healthy"
    },
    "recommendations": {
      "total_vectors": 156,
      "index_size_mb": 8.1,
      "last_updated": "2024-06-04T16:20:00Z",
      "health": "healthy"
    }
  },
  "overall_health": "healthy",
  "embedding_model": "text-embedding-004",
  "vector_dimension": 768,
  "total_storage_mb": 25.1
}
```

#### **POST /api/vectors/rebuild/**
Rebuild all FAISS indexes from scratch (admin operation).

**Prerequisites:** Admin permissions required

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/vectors/rebuild/" \
  -H "Content-Type: application/json" \
  -d '{
    "indexes": ["capabilities", "business_goals", "recommendations"],
    "force": false
  }'
```

**Example Response:**
```json
{
  "status": "rebuild initiated",
  "job_id": "rebuild-2024-06-04-16-50-123",
  "estimated_completion": "2024-06-04T17:05:00Z",
  "indexes_to_rebuild": ["capabilities", "business_goals", "recommendations"],
  "total_items_to_process": 490
}
```

#### **POST /api/vectors/optimize/**
Optimize FAISS indexes for better search performance.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/vectors/optimize/" \
  -H "Content-Type: application/json" \
  -d '{
    "index_type": "capabilities",
    "optimization_level": "standard"
  }'
```

**Response:**
```json
{
  "status": "optimization complete",
  "index_type": "capabilities",
  "performance_improvement": "15%",
  "new_search_time_ms": 23,
  "previous_search_time_ms": 27
}
```

### **5.7. Error Responses**

All API endpoints return consistent error responses:

**Validation Error (400):**
```json
{
  "error": true,
  "message": "Validation error",
  "field_errors": {
    "name": ["This field is required."],
    "description": ["Description must be at least 10 characters long."]
  },
  "status_code": 400
}
```

**Not Found (404):**
```json
{
  "error": true,
  "message": "Resource not found",
  "details": "Capability with id 'invalid-uuid' not found.",
  "status_code": 404
}
```

**Server Error (500):**
```json
{
  "error": true,
  "message": "Internal server error",
  "details": "An unexpected error occurred. Please try again later.",
  "status_code": 500
}
```

### **5.8. File Upload Specifications**

**Supported File Types:** PDF only
**Maximum File Size:** 10MB
**Upload Endpoint:** `/api/business-goals/` (POST)
**Content-Type:** `multipart/form-data`

**Example with curl:**
```bash
# Upload business goal with PDF attachment
curl -X POST http://localhost:8000/api/business-goals/ \
  -F "title=Digital Strategy Implementation" \
  -F "description=Transform our business operations through digital technologies and process automation. This comprehensive plan outlines our 18-month roadmap." \
  -F "pdf_file=@/path/to/business-strategy.pdf"

# Upload without PDF (JSON format)
curl -X POST http://localhost:8000/api/business-goals/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Experience Enhancement", 
    "description": "Improve customer satisfaction scores from 7.5 to 9.0 through enhanced service delivery and digital touchpoints."
  }'

# Check file size before upload (Linux/Mac)
ls -lh /path/to/document.pdf

# Verify PDF file type
file /path/to/document.pdf
```

### **5.9. API Rate Limiting & Performance**

**Current Configuration:**
- No rate limiting (development)
- Pagination: 20 items per page
- Database optimization with proper indexes
- Efficient query handling for hierarchical data

**Production Recommendations:**
- Implement rate limiting (e.g., 100 requests/minute per IP)
- Add caching for frequently accessed data
- Monitor API performance and add alerts

### **5.10. Quick Reference & Testing Commands**

**Setup Commands:**
```bash
# Start the development server
cd backend && python manage.py runserver

# Load test data
cd backend && python create_test_data.py

# Access API documentation
open http://localhost:8000/swagger/
```

**Common Testing Workflows:**
```bash
# 1. Create a new capability
CAPABILITY_ID=$(curl -s -X POST "http://localhost:8000/api/capabilities/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Capability", "description": "Testing API functionality", "status": "PROPOSED", "strategic_importance": "MEDIUM"}' \
  | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

echo "Created capability: $CAPABILITY_ID"

# 2. Submit a business goal
GOAL_ID=$(curl -s -X POST "http://localhost:8000/api/business-goals/" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Goal", "description": "This is a test business goal to validate our API functionality and AI integration capabilities."}' \
  | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

echo "Created goal: $GOAL_ID"

# 3. Analyze the goal with AI
curl -X POST "http://localhost:8000/api/business-goals/$GOAL_ID/analyze/" \
  -H "Content-Type: application/json" \
  -d '{}'

# 4. Get recommendations
curl -X GET "http://localhost:8000/api/business-goals/$GOAL_ID/recommendations/" | head -50

# 5. Query AI assistant
curl -X POST "http://localhost:8000/api/llm/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the relationship between Product Management and Customer Acquisition in our capability map?"}'
```

**Vector Search Testing:**
```bash
# Test capability semantic search
curl -X POST "http://localhost:8000/api/capabilities/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "customer service and support operations", "limit": 5}'

# Test business goal similarity
GOAL_ID=$(curl -s -X GET "http://localhost:8000/api/business-goals/" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
curl -X GET "http://localhost:8000/api/business-goals/$GOAL_ID/similar/?limit=3"

# Test recommendation patterns
curl -X POST "http://localhost:8000/api/recommendations/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "digital transformation capabilities", "limit": 5, "status_filter": ["APPLIED"]}'

# Check vector database status
curl -X GET "http://localhost:8000/api/vectors/status/"
```

**API Health Check:**
```bash
# Test all main endpoints
echo "Testing Capabilities API..."
curl -s http://localhost:8000/api/capabilities/ | head -10

echo "Testing Business Goals API..."
curl -s http://localhost:8000/api/business-goals/ | head -10

echo "Testing Recommendations API..."
curl -s http://localhost:8000/api/recommendations/ | head -10

echo "Testing AI Assistant..."
curl -s -X POST http://localhost:8000/api/llm/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, are you working?"}' | head -10

echo "All APIs tested successfully!"
```

**Response Formatting (Optional):**
```bash
# Install jq for JSON formatting (if available)
curl -s http://localhost:8000/api/capabilities/ | jq '.'

# Alternative: use Python for formatting
curl -s http://localhost:8000/api/capabilities/ | python -m json.tool

# Save response to file for analysis
curl -s http://localhost:8000/api/capabilities/ > capabilities.json
```

### Implementation Steps

#### Phase 1: Project Setup & Environment (Week 1)

1. **Initial Project Setup**
   * Create project directory structure
   * Set up `shell.nix` with required dependencies
   * Initialize git repository
   * Create `.gitignore` file

2. **Backend Setup**
   * Create Django project and app
   * Set up PostgreSQL database
   * Configure Django settings
   * Create initial models (Capability, BusinessGoal, CapabilityRecommendation)
   * Set up Django REST Framework
   * Create basic serializers and views

3. **Frontend Setup**
   * Initialize React project with Vite
   * Set up Shadcn UI and Tailwind CSS
   * Configure project structure
   * Set up routing with React Router
   * Create basic layout components

#### Phase 2: Core Backend Implementation (Week 2)

1. **Database & Models**
   * Implement all Django models
   * Create and run migrations
   * Add model validators and constraints
   * Set up model relationships

2. **API Development**
   * Implement all API endpoints
   * Add authentication (if needed)
   * Set up CORS
   * Add request/response validation
   * Implement error handling

3. **LLM Integration**
   * Set up Gemini API client
   * Implement PDF processing
   * Create prompt engineering templates
   * Add recommendation generation logic
   * Implement recommendation application logic

4. **Vector Database Integration (FAISS)**
   * Install and configure FAISS dependencies
   * Implement VectorManager service class
   * Create VectorEmbedding model and migrations
   * Set up automatic embedding generation via model signals
   * Implement vector search API endpoints
   * Add vector-enhanced LLM context retrieval

#### Phase 3: Frontend Implementation (Week 3)

1. **Core Components**
   * Implement layout and navigation
   * Create reusable UI components
   * Set up state management
   * Implement API integration layer

2. **Feature Pages**
   * Build Capability Map viewer with semantic search
   * Create Goal submission form with smart suggestions
   * Implement Goal analysis interface with similar goals display
   * Build Recommendation management UI with confidence scores
   * Create AI Q&A interface with vector-enhanced context
   * Implement SemanticSearchPage for cross-content search

3. **Vector-Enhanced UI Components**
   * SimilarityIndicator for displaying relevance scores
   * VectorSearchInput for semantic search functionality
   * RecommendationConfidence for showing AI confidence
   * ContextualResults for displaying related items
   * Smart suggestions and auto-complete features

4. **UI/UX Refinement**
   * Add loading states for vector search operations
   * Implement error handling
   * Add success/error notifications
   * Improve responsive design
   * Add animations and transitions

#### Phase 4: Testing & Vector Optimization (Week 4)

1. **Backend Testing**
   * Write unit tests for models
   * Test API endpoints including vector search
   * Validate LLM integration with vector context
   * Test PDF processing
   * Add integration tests for FAISS operations
   * Test vector embedding generation and similarity search

2. **Frontend Testing**
   * Test components including vector search UI
   * Validate form submissions with smart suggestions
   * Test API integration for semantic search
   * Add end-to-end tests for vector-enhanced workflows
   * Test responsive design

3. **Vector Database Optimization**
   * Optimize FAISS index performance
   * Test similarity thresholds and relevance scoring
   * Validate embedding quality and search accuracy
   * Implement index backup and recovery
   * Performance testing for large datasets

4. **Documentation & Deployment**
   * Write API documentation including vector endpoints
   * Create user documentation for semantic search features
   * Set up deployment configuration
   * Prepare deployment scripts
   * Create README files with FAISS setup instructions

#### Phase 5: Launch & Monitoring (Week 5)

1. **Final Testing**
   * Perform security audit
   * Test performance
   * Validate all features
   * Check accessibility
   * Test cross-browser compatibility

2. **Deployment**
   * Deploy backend
   * Deploy frontend
   * Set up monitoring
   * Configure logging
   * Set up error tracking

3. **Post-Launch**
   * Monitor system performance
   * Gather user feedback
   * Fix any issues
   * Plan future improvements

### Development Guidelines

1. **Code Organization**
   * Follow Django best practices for backend
   * Use React best practices for frontend
   * Maintain consistent code style
   * Document complex logic
   * Use meaningful commit messages

2. **Testing Strategy**
   * Write tests for critical functionality
   * Use test-driven development where appropriate
   * Maintain good test coverage
   * Test edge cases
   * Validate error handling

3. **Security Considerations**
   * Validate all inputs
   * Sanitize user data
   * Protect sensitive information
   * Implement rate limiting
   * Follow security best practices

4. **Performance Optimization**
   * Optimize database queries
   * Implement caching where needed
   * Minimize API calls
   * Optimize frontend bundle size
   * Use lazy loading where appropriate

---
---

