# RECOMAI — System Architecture & Technical Specifications

> **"Discover what fits you, powered by intelligence."**  
> Final-Year CSE Project & Portfolio Architecture

RECOMAI is an AI-powered recommendation system designed for technical learning resources, curricula, and tools. This document details the component architecture, data flow, recommendation algorithms, and database design.

---

## 1. High-Level Architecture

```
                                  +-------------------------------------------------------+
                                  |           RECOMAI Modern Frontend (SPA)              |
                                  |  - 16 Connected Views & Dark Glassmorphism Theme     |
                                  |  - Real-Time "Why Recommended" Attribution Modals     |
                                  |  - Interactive Rating, Bookmarking & Search           |
                                  +---------------------------+---------------------------+
                                                              |
                                                      REST APIs / JSON
                                                              |
                                                              v
                                  +-------------------------------------------------------+
                                  |               FastAPI REST Backend                    |
                                  |  - PBKDF2 Cryptographic Security & JWT Auth           |
                                  |  - Candidate Routing & Interaction Handlers           |
                                  |  - Auto-Generated Swagger / OpenAPI Documentation     |
                                  +---------------------------+---------------------------+
                                                              |
                                       +----------------------+----------------------+
                                       |                                             |
                                       v                                             v
                    +------------------------------------+        +------------------------------------+
                    |        PostgreSQL Database         |        |   Multi-Signal Recommendation Pipe  |
                    |  - Relational Storage via ORM      |        |  - Candidate Generator             |
                    |  - Indexed Relations & Timestamps  |        |  - MAX Semantic Representations    |
                    |  - Foreign Keys & Telemetry Logs   |        |  - Mojo Vector Ranking Engine      |
                    +------------------------------------+        |  - Transparent Explainer Engine    |
                                                                  +------------------+-----------------+
                                                                                     |
                                                           +-------------------------+-------------------------+
                                                           |                                                   |
                                                           v                                                   v
                                        +------------------------------------+              +------------------------------------+
                                        |       MAX Semantic Layer           |              |        Mojo Ranking Engine         |
                                        |  - 64-dim Latent Representations   |              |  - Vector Dot Products & L2 Norms  |
                                        |  - Domain Knowledge Clusters       |              |  - Batch Cosine Similarity         |
                                        |  - Conceptual Semantic Search      |              |  - Multi-Signal Candidate Ranking  |
                                        +------------------------------------+              +------------------------------------+
```

---

## 2. Multi-Signal Recommendation Pipeline

### Stage 1: Candidate Generation
To avoid full-table scans, candidate resources are gathered from four complementary signals:
1. **Preference-Based Matching**: Direct category intersection with the user's selected interests from onboarding or profile settings.
2. **Content-Based Matching**: Overlap between the user's preferred skill tags and candidate resource tags.
3. **Interaction-Based Filtering**: Finds resources conceptually related to items the user liked, favorited, or rated $\ge 4.0\star$.
4. **Trending & Quality**: High engagement and strong average ratings provide a reliable foundation for exploration and cold starts.
5. **Deduplication & Exclusion**: Explicitly filters out resources the user has hidden or disliked.

### Stage 2: MAX Semantic Layer
Candidate resources and user interest queries are encoded into normalized 64-dimensional latent semantic vectors via `MaxInferenceService`. Domain keyword clusters project technical concepts into dedicated vector subspaces:
- `ai_ml` (Transformers, Deep Learning, Neural Networks, PyTorch)
- `web_eng` (FastAPI, Microservices, REST APIs, JavaScript)
- `cloud_devops` (Kubernetes, Docker, CI/CD, Containerization)
- `data_eng` (SQL, DuckDB, Columnar Analytics, ETL)
- `cyber_security` (Web Security, Cryptography, Zero-Trust)
- `systems_algo` (Mojo, SIMD, Concurrency, Algorithms)

### Stage 3: Mojo Ranking Engine
The Mojo modules (`similarity.mojo` and `ranker.mojo`) define vector cosine similarity and multi-signal ranking algorithms:
$$\text{CosineSimilarity}(U, I) = \frac{U \cdot I}{\|U\|_2 \cdot \|I\|_2} = \frac{\sum_{k=1}^{64} U_k I_k}{\sqrt{\sum U_k^2} \sqrt{\sum I_k^2}}$$

Candidates are then evaluated using weighted composite scoring:
$$\text{Score} = w_{\text{sem}} \cdot S_{\text{semantic}} + w_{\text{pref}} \cdot S_{\text{preference}} + w_{\text{cat}} \cdot S_{\text{category}} + w_{\text{tag}} \cdot S_{\text{tag}} + w_{\text{rat}} \cdot S_{\text{rating}}$$

A Python orchestration bridge (`bridge.py`) manages native Mojo SDK execution when available, with a built-in mathematical vector fallback.

### Stage 4: Transparent Explanation Engine
Every recommendation includes a plain-English explanation payload:
- **Match Score**: Scaled percentage indicator (e.g. `92% Match`).
- **Headline**: Clear summary (e.g. *"Matches your Artificial Intelligence & Python interests"*).
- **Factor Attributions**: Concrete reasons detailing category alignment, topic match, semantic similarity, and community rating.
- **Factor Weights**: Normalized contribution breakdown across signals.

---

## 3. Database Schema (PostgreSQL)

| Table | Primary Key | Foreign Keys | Key Columns |
| :--- | :--- | :--- | :--- |
| `users` | `id` (int) | - | `email`, `hashed_password`, `full_name`, `role`, `is_active`, `created_at` |
| `user_preferences` | `id` (int) | `user_id` -> `users.id` | `preferred_categories`, `preferred_tags`, `experience_level`, `bio` |
| `categories` | `id` (int) | - | `name`, `slug`, `description`, `icon`, `created_at` |
| `items` | `id` (int) | `category_id` -> `categories.id` | `title`, `slug`, `description`, `content`, `tags`, `difficulty_level`, `rating_avg`, `views_count`, `likes_count` |
| `interactions` | `id` (int) | `user_id`, `item_id` | `interaction_type` (view, like, dislike, hide), `dwell_time_seconds`, `created_at` |
| `ratings` | `id` (int) | `user_id`, `item_id` | `score` (1.0 - 5.0), `review`, `created_at`, `uq_user_item_rating` |
| `favorites` | `id` (int) | `user_id`, `item_id` | `created_at`, `uq_user_item_favorite` |
| `search_history` | `id` (int) | `user_id` (nullable) | `query`, `results_count`, `created_at` |
| `recommendation_logs` | `id` (int) | `user_id`, `item_id` | `score`, `match_percentage`, `explanation`, `strategy`, `created_at` |
