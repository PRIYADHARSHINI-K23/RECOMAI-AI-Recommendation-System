# RECOMAI — Intelligent AI Recommendation System

> **"Discover what fits you, powered by intelligence."**  
> Final-Year Computer Science & Engineering Project

RECOMAI is an AI-powered recommendation system built to demonstrate personalization, semantic understanding, intelligent ranking, and explainable recommendations. Developed as a final-year CSE project and portfolio application, RECOMAI combines a **FastAPI** REST backend, a **PostgreSQL** relational database, a **MAX Semantic Layer**, and a **Mojo Ranking Engine** with a modern web interface.

---

## 🌟 Key Features

- **Personalization**: Builds a dynamic interest profile based on user preferences, searches, ratings, favorites, and interactions.
- **Semantic Understanding**: Uses high-dimensional semantic representations via the MAX Semantic Layer to capture conceptual relationships between topics and queries.
- **Intelligent Ranking**: Combines multiple signals—semantic similarity, user preferences, categories, skill tags, quality ratings, and popularity—to rank resources.
- **Explainable Recommendations**: Every recommendation provides a clear match percentage (e.g. `92% Match`) and explains the exact factors that contributed to the recommendation.
- **Interaction Learning**: Telemetry logging (views, likes, bookmarks, ratings, and searches) continuously updates user affinity and future recommendations.
- **Discover & Semantic Search**: Allows browsing across disciplines with category filters and natural language conceptual search.
- **AI Insights & Telemetry**: Visualizes discipline affinity, interaction metrics, and activity history.
- **Admin Dashboard & Management**: Enables resource management (create, update, delete), user inspection, and platform telemetry monitoring.
- **Cold-Start Handling**: Onboarding interest selection provides immediate relevant recommendations for new users before interaction history is formed.

---

## 🏗️ System Architecture

```
User Action / Query
       ↓
Candidate Generation (Content + Preferences + Interactions + Quality)
       ↓
MAX Semantic Layer (64-dim Latent Representation & Embeddings)
       ↓
Mojo Ranking Engine (Vector Cosine Similarity & Multi-Factor Scoring)
       ↓
Transparent Explanation Engine (Factor Attributions & Match %)
       ↓
FastAPI REST Backend (Endpoints, Validation, PBKDF2 Auth)
       ↓
PostgreSQL Database (ACID Storage, Relations, Telemetry)
       ↓
RECOMAI Frontend (16 Connected Views, Cyber-Dark UI)
```

---

## 🛠️ Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.14 + FastAPI | REST API endpoints, routing, validation, and middleware |
| **Primary Database** | PostgreSQL + SQLAlchemy 2.0 + psycopg3 | Relational tables, referential integrity, and telemetry logs |
| **Semantic Layer** | MAX Semantic Layer (`backend/app/ai/`) | 64-dimensional semantic embeddings and semantic search |
| **Ranking Engine** | Mojo Ranking Engine (`backend/app/mojo/`) | Vector similarity and composite scoring (`.mojo` modules with Python fallback bridge) |
| **Security & Auth** | PBKDF2-HMAC-SHA256 + HMAC JWT | Salted password hashing and token-based authentication |
| **Frontend** | Modern JavaScript (ES6+) + CSS3 | Single-page application, responsive layout, glassmorphism styling |

---

## 📊 Database Schema (PostgreSQL)

The database schema is structured into 9 relational tables:

1. **`users`**: User identities, PBKDF2 hashed passwords, roles (`user`, `admin`), active status.
2. **`user_preferences`**: Preferred category list, skill tags, technical experience level, bio.
3. **`categories`**: Engineering disciplines (Artificial Intelligence, Machine Learning, Web Engineering, Cloud & DevOps, Data Science, Cyber Security, High-Performance Systems, Algorithms & Architecture).
4. **`items`**: Catalog resources, technical tags, descriptions, difficulty, and quality metrics (`rating_avg`, `rating_count`, `views_count`, `likes_count`).
5. **`interactions`**: Behavioral events (`view`, `like`, `dislike`, `hide`) with dwell times.
6. **`ratings`**: 1.0 to 5.0 star user ratings with a unique constraint on `(user_id, item_id)`.
7. **`favorites`**: Saved bookmarks with a unique constraint on `(user_id, item_id)`.
8. **`search_history`**: Timestamped query log for user interest learning.
9. **`recommendation_logs`**: Historical recommendation scores and explanations for auditability.

---

## 🎯 Recommendation Methodology

### 1. Candidate Generation
Candidates are drawn from four complementary sources:
- **Preference-Based**: Direct matches with categories selected in user onboarding or profile.
- **Content-Based**: Overlap between user skill tags and candidate resource tags.
- **Interaction-Based**: Resources conceptually related to items the user liked, favorited, or rated $\ge 4.0\star$.
- **Trending & Quality**: High engagement and strong ratings provide a solid baseline for exploration and cold starts.
- **Exclusion**: Items previously disliked or hidden are excluded from recommendations.

### 2. MAX Semantic Layer
`MaxInferenceService` computes normalized 64-dimensional latent semantic representations. Domain clusters (AI/ML, Web, Cloud, Data, Security, Systems) map conceptual affinity into vector space, enabling semantic matching even when search queries use different vocabulary.

### 3. Mojo Ranking Engine
The Mojo modules (`similarity.mojo` and `ranker.mojo`) define vectorized cosine similarity and multi-factor composite ranking:
$$\text{Score} = w_{\text{sem}} \cdot S_{\text{semantic}} + w_{\text{pref}} \cdot S_{\text{preference}} + w_{\text{cat}} \cdot S_{\text{category}} + w_{\text{tag}} \cdot S_{\text{tag}} + w_{\text{rat}} \cdot S_{\text{rating}} + w_{\text{pop}} \cdot S_{\text{popularity}}$$
Final ranking weights vary by recommendation strategy:

- Preference: semantic 0.15, preference 0.45, category 0.15, tag overlap 0.10, rating 0.05, popularity 0.10
- Trending: semantic 0.15, preference 0.10, category 0.10, tag overlap 0.05, rating 0.50, popularity 0.10
- Hybrid: semantic 0.30, preference 0.25, category 0.15, tag overlap 0.15, rating 0.10, popularity 0.05

Popularity is normalized using platform engagement:
popularity_score = min(1.0, views_count × 0.05 + likes_count × 0.10)
The resulting popularity score ranges from 0 to 1 and contributes to the final recommendation score according to the selected strategy.
A Python orchestration bridge (`bridge.py`) checks for native Mojo SDK availability and executes the mathematical vector calculations, maintaining seamless execution across platforms.

### 4. Transparent Explanation Engine
Every recommendation includes:
- **Match Score**: Scaled percentage indicator (e.g. `92% Match`).
- **Explanation Headline**: Clear summary (e.g. *"Matches your Artificial Intelligence and Python interests"*).
- **Factor Attributions**: Concrete bullet points detailing category relevance, topic tags, semantic similarity, and community ratings.
- **Signal Breakdown**: Normalized factor contribution bars (0–100%).

---

## 🚀 Running the Project

### 1. Configuration
The application reads environment variables from `.env`. Default configuration connects to PostgreSQL with an automatic local SQLite fallback for seamless development:
```ini
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/recomai"
SECRET_KEY="recomai-secret-key-cse-portfolio-2026"
```

### 2. Database Initialization
Initialize schema tables and seed sample curricula:
```bash
python scripts/init_db.py
```

### 3. Start Development Server
Launch the FastAPI application:
```bash
python scripts/run_dev.py
```
- **Web Application**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8000/docs`

---

## 🧪 Automated Testing

Run the automated test suite verifying all core systems:
```bash
`python -m unittest discover -s tests`
```
Test suite coverage:
- Health check and diagnostic endpoints
- MAX semantic embedding generation and L2 normalization
- Mojo vector cosine similarity calculations
- User registration, login, and JWT validation
- Personalized dashboard recommendations and explanation payloads
- Semantic natural language search
- Likes, bookmarks, and star ratings telemetry
- AI Insights affinity breakdown
- Administrator analytics and catalog management

---

## 🎬 Presentation & Demo Workflow

1. **Sign In**:
   - Student Account: `demo@recomai.io` / `Demo@123`
   - Admin Account: `admin@recomai.io` / `Admin@123`
2. **Dashboard**: View personalized recommendations grouped into "Recommended For You", "Trending", "Based On Interests", and "Recently Viewed".
3. **Why Recommended**: Click **"Why?"** on any card to view the match percentage and explicit factor attributions.
4. **Interactivity**: Rate an item with 1–5 stars, click the heart to like, or bookmark for later.
5. **Discover & Semantic Search**: Search using natural language queries (e.g. *"courses for learning programming with Python"*).
6. **AI Insights**: Inspect the 4-step architecture flow diagram, category affinity breakdown, and chronological activity timeline.
7. **Admin Portal**: Log in with administrator credentials to view telemetry metrics, manage catalog items, and view registered users.

---

## 📄 License & Attribution

Developed as a Final-Year Computer Science & Engineering Capstone Project.
