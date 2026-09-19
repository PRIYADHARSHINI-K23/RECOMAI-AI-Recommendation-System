# RECOMAI — REST API Specifications

The RECOMAI backend is built with FastAPI. Interactive OpenAPI/Swagger documentation is hosted automatically at `/docs`.

Base URL: `http://localhost:8000/api/v1`

---

## 1. Authentication Endpoints

### `POST /auth/register`
Creates a new user account and default preferences.
- **Request Body**:
  ```json
  {
    "full_name": "Alex Chen",
    "email": "alex@example.com",
    "password": "Password123",
    "role": "user",
    "preferred_categories": ["Artificial Intelligence"],
    "experience_level": "Intermediate"
  }
  ```
- **Response**: `201 Created` with JWT access token and user profile.

### `POST /auth/login`
Authenticates credentials and returns a JWT bearer token.
- **Request Body**:
  ```json
  {
    "email": "demo@recomai.io",
    "password": "Demo@123"
  }
  ```
- **Response**: `200 OK` with token and user object.

### `GET /auth/me`
Retrieves the authenticated user profile.
- **Headers**: `Authorization: Bearer <token>`

### `PUT /auth/preferences`
Updates user categories, tags, and experience level.

---

## 2. Items & Categories Endpoints

### `GET /items/categories`
Lists all categories with active resource counts.

### `GET /items`
Lists resources with optional query filters:
- `category_id` (int)
- `category_slug` (str)
- `tag` (str)
- `difficulty` (Beginner | Intermediate | Advanced)
- `sort_by` (popular | rating | newest | title)

### `GET /items/{id}`
Retrieves complete details for a single item and records view telemetry.

---

## 3. Recommendation Endpoints

### `GET /recommendations/dashboard`
Returns five structured feeds:
1. `recommended_for_you`: Multi-signal hybrid recommendations.
2. `trending_for_you`: Community velocity and bookmark momentum.
3. `based_on_interests`: Direct match with user profile categories.
4. `recently_viewed`: Chronological session history.
5. `popular_items`: High-view resources for cold-start exploration.

### `GET /recommendations/feed?strategy=...`
Custom feed by strategy (`hybrid`, `preference`, `trending`, `interaction`).

### `GET /recommendations/item/{id}/related`
Finds semantically similar resources using MAX cosine distance.

### `GET /recommendations/status`
Returns runtime diagnostic status of MAX Inference and Mojo engines.

---

## 4. Semantic Search

### `GET /search?q={query}`
Performs MAX-embedded vector semantic search combined with keyword indexing.

---

## 5. Interactions & Feedback

### `POST /interactions`
Logs view events and dwell times.

### `POST /interactions/like/{item_id}`
Toggles item like state.

### `POST /interactions/favorite/{item_id}`
Toggles bookmark state.

### `POST /interactions/rate`
Submits a 1-5 star rating and review.

### `GET /interactions/favorites`
Lists all items saved by the current user.

---

## 6. AI Insights

### `GET /insights/me`
Returns category affinity percentages, interaction metrics, cognitive domain breakdown, and recent activity stream.

---

## 7. Administrator Portal

### `GET /admin/analytics`
Telemetry metrics, top viewed/liked/recommended items, and platform stats.

### `GET /admin/items`
Lists all resources for admin inspection.

### `POST /admin/items`
Creates a new resource.

### `PUT /admin/items/{id}`
Updates an existing resource.

### `DELETE /admin/items/{id}`
Deletes a resource.

### `GET /admin/users`
Lists all registered users.
