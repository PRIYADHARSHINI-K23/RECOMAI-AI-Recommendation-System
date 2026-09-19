"""Comprehensive End-to-End Test Suite for RECOMAI.
Tests authentication, recommendations, MAX embeddings, Mojo similarity, and admin functions.
"""
import sys
import unittest
from pathlib import Path

# Add project root and backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db, SessionLocal
from app.database.seed_data import seed_database
from app.ai.max_service import max_service
from app.mojo.bridge import mojo_bridge
from app.recommendation.ranker import recommendation_ranker

class TestRecomaiSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize and seed database
        init_db()
        with SessionLocal() as db:
            seed_database(db)
        cls.client = TestClient(app)

    def test_01_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["project"], "RECOMAI")
        self.assertIn("database", data)
        self.assertIn("max_ai", data)
        self.assertIn("mojo", data)

    def test_02_engine_status(self):
        response = self.client.get("/api/v1/recommendations/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project"], "RECOMAI")
        self.assertIn("max_engine", data)
        self.assertIn("mojo_engine", data)
        self.assertIn("pipeline_stages", data)

    def test_03_max_embeddings_unit(self):
        text = "deep learning neural network pytorch"
        embedding = max_service.generate_embedding(text)
        self.assertEqual(len(embedding), 64)
        # Verify L2 normalization
        norm = sum(x * x for x in embedding) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=2)

    def test_04_mojo_similarity_unit(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        sim_identical = mojo_bridge.cosine_similarity(v1, v2)
        sim_orthogonal = mojo_bridge.cosine_similarity(v1, v3)
        self.assertAlmostEqual(sim_identical, 1.0, places=3)
        self.assertAlmostEqual(sim_orthogonal, 0.0, places=3)

    def test_05_demo_user_login(self):
        response = self.client.post("/api/v1/auth/login", json={
            "email": "demo@recomai.io",
            "password": "Demo@123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "demo@recomai.io")
        self.__class__.demo_token = data["access_token"]

    def test_06_admin_user_login(self):
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@recomai.io",
            "password": "Admin@123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["role"], "admin")
        self.__class__.admin_token = data["access_token"]

    def test_07_categories_and_items(self):
        cat_resp = self.client.get("/api/v1/items/categories")
        self.assertEqual(cat_resp.status_code, 200)
        categories = cat_resp.json()
        self.assertGreaterEqual(len(categories), 8)

        items_resp = self.client.get("/api/v1/items")
        self.assertEqual(items_resp.status_code, 200)
        items = items_resp.json()
        self.assertGreaterEqual(len(items), 15)

    def test_08_personalized_dashboard_recommendations(self):
        headers = {"Authorization": f"Bearer {self.demo_token}"}
        resp = self.client.get("/api/v1/recommendations/dashboard", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("recommended_for_you", data)
        self.assertIn("trending_for_you", data)
        self.assertIn("based_on_interests", data)
        
        # Verify recommendation structure & explanations
        first_rec = data["recommended_for_you"][0]
        self.assertIn("item", first_rec)
        self.assertIn("match_percentage", first_rec)
        self.assertIn("explanation", first_rec)
        self.assertIn("headline", first_rec["explanation"])
        self.assertIn("reasons", first_rec["explanation"])

    def test_09_semantic_search(self):
        resp = self.client.get("/api/v1/search?q=neural+networks+deep+learning")
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertGreater(len(results), 0)
        top_hit = results[0]
        self.assertIn("explanation", top_hit)
        self.assertIn("match_percentage", top_hit)

    def test_10_interactions(self):
        headers = {"Authorization": f"Bearer {self.demo_token}"}
        
        # Like toggle
        like_resp = self.client.post("/api/v1/interactions/like/1", headers=headers)
        self.assertEqual(like_resp.status_code, 200)
        
        # Favorite toggle
        fav_resp = self.client.post("/api/v1/interactions/favorite/1", headers=headers)
        self.assertEqual(fav_resp.status_code, 200)

        # Rate item
        rate_resp = self.client.post("/api/v1/interactions/rate", headers=headers, json={
            "item_id": 1,
            "score": 5.0,
            "review": "Excellent architectural explanation!"
        })
        self.assertEqual(rate_resp.status_code, 200)

    def test_11_user_ai_insights(self):
        headers = {"Authorization": f"Bearer {self.demo_token}"}
        resp = self.client.get("/api/v1/insights/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("top_categories", data)
        self.assertIn("affinity_radar", data)
        self.assertIn("interaction_stats", data)
        self.assertIn("recent_activity", data)
        if data["recent_activity"]:
            for act in data["recent_activity"]:
                self.assertIn("T", act["timestamp"])
                self.assertTrue(act["timestamp"].endswith("Z"))

    def test_12_admin_analytics(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.get("/api/v1/admin/analytics", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["total_users"], 0)
        self.assertGreater(data["total_items"], 0)



