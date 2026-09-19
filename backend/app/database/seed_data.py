import logging
from sqlalchemy.orm import Session
from app.models.user import User, UserPreferences
from app.models.item import Category, Item
from app.models.interaction import Interaction, Rating, Favorite, SearchHistory
from app.auth.security import hash_password

logger = logging.getLogger("recomai.seed")

CATEGORIES_DATA = [
    {
        "name": "Artificial Intelligence",
        "slug": "ai",
        "description": "Transformers, LLMs, Neural Networks, Computer Vision, and Generative AI systems.",
        "icon": "brain"
    },
    {
        "name": "Machine Learning",
        "slug": "machine-learning",
        "description": "Supervised, unsupervised, reinforcement learning algorithms, PyTorch, and Scikit-Learn.",
        "icon": "cpu"
    },
    {
        "name": "Web Engineering",
        "slug": "web-engineering",
        "description": "Modern full-stack architectures, FastAPI, microservices, reactive frontends, and REST APIs.",
        "icon": "globe"
    },
    {
        "name": "Cloud & DevOps",
        "slug": "cloud-devops",
        "description": "Containerization, Kubernetes, CI/CD automation pipelines, Docker, and AWS cloud architecture.",
        "icon": "cloud"
    },
    {
        "name": "Data Science",
        "slug": "data-science",
        "description": "Statistical modeling, exploratory data analysis, Pandas, SQL data warehousing, and ETL pipelines.",
        "icon": "database"
    },
    {
        "name": "Cyber Security",
        "slug": "cybersecurity",
        "description": "Zero-trust network defense, penetration testing, cryptography, web security, and vulnerability auditing.",
        "icon": "shield"
    },
    {
        "name": "High-Performance Systems",
        "slug": "systems-mojo",
        "description": "Mojo programming, SIMD parallelism, C++, concurrency, low-level memory control, and GPU kernels.",
        "icon": "zap"
    },
    {
        "name": "Algorithms & Architecture",
        "slug": "algorithms",
        "description": "Core data structures, graph theory, dynamic programming, distributed consensus, and system design.",
        "icon": "code"
    }
]

ITEMS_DATA = [
    # Artificial Intelligence
    {
        "title": "Mastering Transformers & Attention Mechanisms",
        "slug": "mastering-transformers-attention",
        "category_slug": "ai",
        "description": "An exhaustive guide to modern transformer architecture, multi-head self-attention, and positional embeddings.",
        "content": "Deep dive into building transformer encoders and decoders from scratch using PyTorch. Understand QKV projections and cross-attention.",
        "tags": ["ai", "transformers", "nlp", "deep-learning", "pytorch", "python"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.9,
        "rating_count": 142,
        "views_count": 1280,
        "likes_count": 310,
        "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Building Production LLM Applications with LangChain & Vector DBs",
        "slug": "production-llm-langchain-vectordb",
        "category_slug": "ai",
        "description": "Architect scalable Retrieval-Augmented Generation (RAG) pipelines with semantic search, embeddings, and vector databases.",
        "content": "Learn how to build hybrid search pipelines combining BM25 and dense vector embeddings with rerankers and contextual memory.",
        "tags": ["ai", "llm", "rag", "langchain", "embeddings", "vector-db", "python"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.8,
        "rating_count": 98,
        "views_count": 950,
        "likes_count": 240,
        "image_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Computer Vision with PyTorch & YOLOv8",
        "slug": "computer-vision-pytorch-yolo",
        "category_slug": "ai",
        "description": "Real-time object detection, image segmentation, and convolutional neural network design for edge robotics.",
        "content": "Covers CNN backbones, feature pyramid networks, loss functions for object detection, and deployment to mobile/edge devices.",
        "tags": ["ai", "computer-vision", "pytorch", "yolo", "cnn", "python"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.7,
        "rating_count": 86,
        "views_count": 810,
        "likes_count": 195,
        "image_url": "https://images.unsplash.com/photo-1555255707-c07966088b7b?auto=format&fit=crop&w=600&q=80"
    },

    # Machine Learning
    {
        "title": "Deep Learning Specialization: Neural Networks & Backprop",
        "slug": "deep-learning-neural-networks-backprop",
        "category_slug": "machine-learning",
        "description": "Understand gradient descent mathematics, computational graphs, matrix calculus, and weight initialization strategies.",
        "content": "Mathematical derivations of Adam, RMSprop, Xavier initialization, and batch normalization implemented in clean Python.",
        "tags": ["machine-learning", "deep-learning", "math", "algorithms", "python"],
        "difficulty_level": "Beginner",
        "rating_avg": 4.95,
        "rating_count": 230,
        "views_count": 2100,
        "likes_count": 520,
        "image_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Scikit-Learn Pipeline Design & Feature Engineering",
        "slug": "scikit-learn-pipelines-feature-engineering",
        "category_slug": "machine-learning",
        "description": "Best practices for preventing data leakage, imputing missing values, cross-validation, and hyperparameter tuning.",
        "content": "Production pipelines utilizing ColumnTransformer, target encoding, randomized grid search, and custom sklearn estimators.",
        "tags": ["machine-learning", "scikit-learn", "feature-engineering", "python", "data-science"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.6,
        "rating_count": 75,
        "views_count": 730,
        "likes_count": 160,
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Reinforcement Learning with Q-Learning & Actor-Critic",
        "slug": "reinforcement-learning-actor-critic",
        "category_slug": "machine-learning",
        "description": "Markov Decision Processes, policy gradients, PPO, and autonomous agent training in simulated Gym environments.",
        "content": "Implement Deep Q-Networks (DQN) with replay buffers, target networks, and advantage actor-critic (A2C) models.",
        "tags": ["machine-learning", "reinforcement-learning", "pytorch", "python", "algorithms"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.85,
        "rating_count": 64,
        "views_count": 620,
        "likes_count": 180,
        "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80"
    },

    # Web Engineering
    {
        "title": "High-Performance REST APIs with FastAPI & PostgreSQL",
        "slug": "fastapi-postgresql-rest-api",
        "category_slug": "web-engineering",
        "description": "Build asynchronous, typed, production RESTful web services with SQLAlchemy 2.0, Pydantic, and connection pooling.",
        "content": "Complete guide on async database sessions, dependency injection, OAuth2 security, rate-limiting, and auto-generated OpenAPI.",
        "tags": ["web-engineering", "fastapi", "postgresql", "python", "backend", "api"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.92,
        "rating_count": 180,
        "views_count": 1650,
        "likes_count": 410,
        "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Microservices Architecture with Docker & Event Brokers",
        "slug": "microservices-docker-event-brokers",
        "category_slug": "web-engineering",
        "description": "Design decoupled, resilient microservices communicating through Kafka/RabbitMQ and API Gateways.",
        "content": "Pattern catalog covering CQRS, Saga distributed transactions, outbox pattern, circuit breakers, and distributed tracing.",
        "tags": ["web-engineering", "microservices", "docker", "cloud-devops", "backend"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.75,
        "rating_count": 110,
        "views_count": 1120,
        "likes_count": 290,
        "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Modern Frontend Architecture & Reactive State Management",
        "slug": "modern-frontend-reactive-state",
        "category_slug": "web-engineering",
        "description": "Component design systems, responsive glassmorphism, accessibility standards, and performant DOM updates.",
        "content": "Mastering client-side routing, optimistic UI updates, debouncing, CSS variables, and modern visual aesthetics.",
        "tags": ["web-engineering", "frontend", "javascript", "css", "ui-ux"],
        "difficulty_level": "Beginner",
        "rating_avg": 4.65,
        "rating_count": 92,
        "views_count": 890,
        "likes_count": 210,
        "image_url": "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=600&q=80"
    },

    # Cloud & DevOps
    {
        "title": "Kubernetes in Production: Clusters, Ingress & Helm",
        "slug": "kubernetes-production-ingress-helm",
        "category_slug": "cloud-devops",
        "description": "Container orchestration at enterprise scale. Pod autoscaling, persistent volumes, and GitOps deployments.",
        "content": "Hands-on guide to writing Helm charts, configuring NGINX ingress controllers, cert-manager SSL, and zero-downtime rollouts.",
        "tags": ["cloud-devops", "kubernetes", "docker", "devops", "cloud"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.88,
        "rating_count": 135,
        "views_count": 1400,
        "likes_count": 340,
        "image_url": "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Docker Deep Dive: Multi-Stage Builds & Security Hardening",
        "slug": "docker-multistage-builds-security",
        "category_slug": "cloud-devops",
        "description": "Optimize image sizes by 90%, leverage buildkit caching, rootless containers, and vulnerability scanning.",
        "content": "Learn how to build minimal alpine and distroless production images for Python, Go, and Node applications with Trivy scans.",
        "tags": ["cloud-devops", "docker", "devops", "security", "linux"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.8,
        "rating_count": 115,
        "views_count": 1250,
        "likes_count": 300,
        "image_url": "https://images.unsplash.com/photo-1607799279861-4dd421887fb3?auto=format&fit=crop&w=600&q=80"
    },

    # Data Science
    {
        "title": "Modern Data Engineering with SQL, DuckDB & Parquet",
        "slug": "data-engineering-duckdb-parquet",
        "category_slug": "data-science",
        "description": "Lightning-fast in-process analytical query execution, columnar storage, and lakehouse architectures.",
        "content": "Transitioning from slow row-based queries to vectorized columnar execution on billion-row datasets using DuckDB and Polars.",
        "tags": ["data-science", "sql", "duckdb", "parquet", "python", "analytics"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.85,
        "rating_count": 105,
        "views_count": 1030,
        "likes_count": 270,
        "image_url": "https://images.unsplash.com/photo-1543286386-713bdd548da4?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Statistical Inference & Predictive Modeling",
        "slug": "statistical-inference-predictive-modeling",
        "category_slug": "data-science",
        "description": "Hypothesis testing, A/B experiment design, Bayesian probability, and generalized linear models.",
        "content": "Practical guide to statistical power calculation, sample size determination, ANOVA, logistic regression, and Bayesian updating.",
        "tags": ["data-science", "statistics", "math", "python", "analytics"],
        "difficulty_level": "Beginner",
        "rating_avg": 4.7,
        "rating_count": 78,
        "views_count": 760,
        "likes_count": 180,
        "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=600&q=80"
    },

    # Cyber Security
    {
        "title": "Practical Web Application Penetration Testing",
        "slug": "web-application-penetration-testing",
        "category_slug": "cybersecurity",
        "description": "OWASP Top 10 vulnerabilities, SQL injection, XSS, CSRF, JWT tampering, and defensive countermeasures.",
        "content": "Learn how attackers discover and exploit broken access control, server-side request forgery (SSRF), and implement defense in depth.",
        "tags": ["cybersecurity", "security", "penetration-testing", "web-engineering", "owasp"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.9,
        "rating_count": 150,
        "views_count": 1580,
        "likes_count": 420,
        "image_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Applied Cryptography & Zero-Knowledge Proofs",
        "slug": "applied-cryptography-zk-proofs",
        "category_slug": "cybersecurity",
        "description": "Elliptic curve cryptography, public key infrastructure, symmetric ciphers, and zk-SNARK fundamentals.",
        "content": "Explore AES-GCM, Diffie-Hellman key exchanges, digital signatures, and verifiable computation with zk-SNARKs.",
        "tags": ["cybersecurity", "cryptography", "security", "math", "algorithms"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.82,
        "rating_count": 68,
        "views_count": 690,
        "likes_count": 190,
        "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80"
    },

    # High-Performance Systems & Mojo
    {
        "title": "Mojo Programming: Fast AI Systems with SIMD & Hardware Acceleration",
        "slug": "mojo-programming-simd-hardware",
        "category_slug": "systems-mojo",
        "description": "Harness the syntax of Python combined with the speed of C. Writing vectorized SIMD kernels and custom hardware ops.",
        "content": "Deep exploration of Mojo types, ownership models, borrowing, SIMD vectorization, parallelize primitives, and MAX engine integration.",
        "tags": ["systems-mojo", "mojo", "ai", "performance", "simd", "systems"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.98,
        "rating_count": 160,
        "views_count": 1750,
        "likes_count": 480,
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Systems Programming: Concurrency, Memory & Cache Coherence",
        "slug": "systems-programming-concurrency-cache",
        "category_slug": "systems-mojo",
        "description": "CPU cache hierarchies (L1/L2/L3), memory barriers, lock-free queues, and cache-friendly data structures.",
        "content": "Designing high-frequency trading and low-latency message queues using false sharing prevention, CAS operations, and ring buffers.",
        "tags": ["systems-mojo", "concurrency", "performance", "algorithms", "systems"],
        "difficulty_level": "Advanced",
        "rating_avg": 4.87,
        "rating_count": 84,
        "views_count": 820,
        "likes_count": 220,
        "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80"
    },

    # Algorithms & Architecture
    {
        "title": "Advanced Data Structures & Competitive Graph Algorithms",
        "slug": "advanced-data-structures-graph-algorithms",
        "category_slug": "algorithms",
        "description": "Segment trees, Fenwick trees, Disjoint Set Union, Dijkstra, Bellman-Ford, Tarjan's SCC, and Network Flow.",
        "content": "Comprehensive implementations and computational complexity proofs for classical algorithms in technical interview problem solving.",
        "tags": ["algorithms", "data-structures", "graphs", "python", "competitive-programming"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.93,
        "rating_count": 210,
        "views_count": 1980,
        "likes_count": 490,
        "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "System Design: Scalable Distributed Systems Architecture",
        "slug": "system-design-scalable-distributed-systems",
        "category_slug": "algorithms",
        "description": "Consistent hashing, database sharding, replication topologies, CDN caching, and rate limiting algorithms.",
        "content": "Designing high-scale platforms like Netflix streaming, Twitter feeds, Uber geo-spatial indexing, and WhatsApp real-time messaging.",
        "tags": ["algorithms", "system-design", "distributed-systems", "architecture", "web-engineering"],
        "difficulty_level": "Intermediate",
        "rating_avg": 4.91,
        "rating_count": 195,
        "views_count": 1840,
        "likes_count": 460,
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80"
    }
]

def seed_database(db: Session):
    """Seed initial categories, items, users, and realistic interaction history."""
    # 1. Seed Categories
    category_map = {}
    for c_data in CATEGORIES_DATA:
        cat = db.query(Category).filter(Category.slug == c_data["slug"]).first()
        if not cat:
            cat = Category(
                name=c_data["name"],
                slug=c_data["slug"],
                description=c_data["description"],
                icon=c_data["icon"]
            )
            db.add(cat)
            db.flush()
        category_map[cat.slug] = cat

    # 2. Seed Items
    item_map = {}
    for i_data in ITEMS_DATA:
        item = db.query(Item).filter(Item.slug == i_data["slug"]).first()
        cat = category_map.get(i_data["category_slug"])
        if not item and cat:
            item = Item(
                title=i_data["title"],
                slug=i_data["slug"],
                category_id=cat.id,
                description=i_data["description"],
                content=i_data["content"],
                tags=i_data["tags"],
                difficulty_level=i_data["difficulty_level"],
                rating_avg=i_data["rating_avg"],
                rating_count=i_data["rating_count"],
                views_count=i_data["views_count"],
                likes_count=i_data["likes_count"],
                image_url=i_data["image_url"]
            )
            db.add(item)
            db.flush()
        if item:
            item_map[item.slug] = item

    # 3. Seed Default Admin User
    admin = db.query(User).filter(User.email == "admin@recomai.io").first()
    if not admin:
        admin = User(
            email="admin@recomai.io",
            hashed_password=hash_password("Admin@123"),
            full_name="RECOMAI Administrator",
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.flush()
        admin_prefs = UserPreferences(
            user_id=admin.id,
            preferred_categories=["Artificial Intelligence", "High-Performance Systems"],
            preferred_tags=["ai", "mojo", "fastapi", "systems"],
            experience_level="Advanced",
            bio="Lead Administrator and AI Systems Engineer for RECOMAI."
        )
        db.add(admin_prefs)

    # 4. Seed Demo Student User
    demo_user = db.query(User).filter(User.email == "demo@recomai.io").first()
    if not demo_user:
        demo_user = User(
            email="demo@recomai.io",
            hashed_password=hash_password("Demo@123"),
            full_name="Alex Chen (CSE Senior)",
            role="user",
            is_active=True
        )
        db.add(demo_user)
        db.flush()
        demo_prefs = UserPreferences(
            user_id=demo_user.id,
            preferred_categories=["Artificial Intelligence", "Web Engineering", "High-Performance Systems"],
            preferred_tags=["ai", "python", "fastapi", "machine-learning", "mojo"],
            experience_level="Intermediate",
            bio="Final-year CSE student exploring AI recommendation architectures and fullstack systems."
        )
        db.add(demo_prefs)

        # Add initial interaction signals for demo user
        t_item1 = item_map.get("mastering-transformers-attention")
        t_item2 = item_map.get("fastapi-postgresql-rest-api")
        t_item3 = item_map.get("mojo-programming-simd-hardware")
        t_item4 = item_map.get("deep-learning-neural-networks-backprop")

        if t_item1:
            db.add(Interaction(user_id=demo_user.id, item_id=t_item1.id, interaction_type="like"))
            db.add(Interaction(user_id=demo_user.id, item_id=t_item1.id, interaction_type="view", dwell_time_seconds=65.0))
            db.add(Favorite(user_id=demo_user.id, item_id=t_item1.id))
            db.add(Rating(user_id=demo_user.id, item_id=t_item1.id, score=5.0, review="Incredible deep dive into self-attention!"))
        
        if t_item2:
            db.add(Interaction(user_id=demo_user.id, item_id=t_item2.id, interaction_type="like"))
            db.add(Interaction(user_id=demo_user.id, item_id=t_item2.id, interaction_type="view", dwell_time_seconds=80.0))
            db.add(Favorite(user_id=demo_user.id, item_id=t_item2.id))
            db.add(Rating(user_id=demo_user.id, item_id=t_item2.id, score=5.0, review="The cleanest FastAPI and async SQLAlchemy setup."))

        if t_item3:
            db.add(Interaction(user_id=demo_user.id, item_id=t_item3.id, interaction_type="view", dwell_time_seconds=45.0))
            db.add(Rating(user_id=demo_user.id, item_id=t_item3.id, score=5.0, review="Mojo's SIMD speeds are mind-blowing."))

        if t_item4:
            db.add(Interaction(user_id=demo_user.id, item_id=t_item4.id, interaction_type="view", dwell_time_seconds=50.0))

        # Add sample search queries
        db.add(SearchHistory(user_id=demo_user.id, query="transformer attention mechanisms", results_count=5))
        db.add(SearchHistory(user_id=demo_user.id, query="fastapi async postgresql", results_count=6))

    db.commit()
    logger.info("Database seeding completed successfully with categories, items, and demo profiles.")
