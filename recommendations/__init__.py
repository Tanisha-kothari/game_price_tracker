"""Recommendations module — deal intelligence."""
from recommendations.engine import RecommendationEngine, DealRecommendation
from recommendations.sale_detector import SaleDetector

__all__ = ["RecommendationEngine", "DealRecommendation", "SaleDetector"]
