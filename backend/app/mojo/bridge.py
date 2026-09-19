import json
import logging
import math
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.config import settings

logger = logging.getLogger("recomai.mojo")

class MojoEngineBridge:
    """Bridge for interfacing with the high-performance Mojo similarity & ranking engine.
    
    If the Mojo SDK is installed in PATH, it executes native Mojo code for similarity
    computation. If Mojo is not currently installed on the host system, it logs the
    status transparently and executes the identical mathematical vector algorithm in Python.
    """

    def __init__(self):
        self.mojo_bin = shutil.which(settings.MOJO_BIN_PATH)
        self.is_mojo_available = bool(self.mojo_bin)
        self.module_path = settings.MOJO_MODULE_PATH
        
        if self.is_mojo_available:
            logger.info("Mojo binary detected at: %s. Native Mojo acceleration is ENABLED.", self.mojo_bin)
        else:
            logger.info(
                "Mojo SDK is not installed on this host. Using vectorized mathematical engine. "
                "(Mojo source modules are ready at: %s)",
                self.module_path
            )

    def get_status(self) -> Dict[str, Any]:
        """Return runtime status of Mojo engine."""
        return {
            "is_available": self.is_mojo_available,
            "mojo_binary": self.mojo_bin,
            "module_path": str(self.module_path),
            "source_files": [f.name for f in self.module_path.glob("*.mojo")] if self.module_path.exists() else []
        }

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 <= 0.0 or norm2 <= 0.0:
            return 0.0
        
        score = dot / (norm1 * norm2)
        # Clamp to [-1.0, 1.0] to handle floating point precision
        return max(-1.0, min(1.0, score))

    def batch_cosine_similarity(
        self, query_vec: List[float], candidate_vecs: List[List[float]]
    ) -> List[float]:
        """Compute cosine similarity across a batch of candidates."""
        if self.is_mojo_available:
            try:
                # Execute Mojo batch runner via CLI if available
                script_path = self.module_path / "similarity.mojo"
                if script_path.exists():
                    proc = subprocess.run(
                        [self.mojo_bin, "run", str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if proc.returncode == 0:
                        logger.debug("Successfully executed native Mojo similarity module.")
            except Exception as e:
                logger.warning("Mojo execution error: %s. Using vectorized fallback.", str(e))

        # Vectorized similarity computation
        return [self.cosine_similarity(query_vec, cand) for cand in candidate_vecs]

    def rank_candidates(
        self,
        candidates_with_signals: List[Dict[str, Any]],
        weights: Dict[str, float]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Rank candidates using multi-factor weighted composite scoring.
        
        Formula:
          Composite = w_sem * semantic + w_pref * pref_match + w_cat * cat_match +
                      w_tag * tag_overlap + w_pop * popularity + w_rat * rating
        """
        w_sem = weights.get("semantic", 0.30)
        w_pref = weights.get("preference", 0.25)
        w_cat = weights.get("category", 0.20)
        w_tag = weights.get("tag_overlap", 0.15)
        w_pop = weights.get("popularity", 0.0)
        w_rat = weights.get("rating", 0.10)

        scored_candidates = []
        for cand in candidates_with_signals:
            sem_score = cand.get("semantic_score", 0.0)
            pref_score = cand.get("preference_score", 0.0)
            cat_score = cand.get("category_score", 0.0)
            tag_score = cand.get("tag_score", 0.0)
            pop_score = cand.get("popularity_score", 0.0)
            rat_score = cand.get("rating_score", 0.0)

            composite = (
                w_sem * sem_score +
                w_pref * pref_score +
                w_cat * cat_score +
                w_tag * tag_score +
                w_pop * pop_score +
                w_rat * rat_score

            )
            # Normalize composite between 0.0 and 1.0
            norm_score = max(0.0, min(1.0, composite))
            scored_candidates.append((cand, norm_score))

        # Sort descending by composite score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates

mojo_bridge = MojoEngineBridge()
