"""Main API router for Acquisitor v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import analysis, companies, pain_points, product_ideas, reporting, research, validation

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(pain_points.router, prefix="/pain-points", tags=["pain-points"])
api_router.include_router(product_ideas.router, prefix="/product-ideas", tags=["product-ideas"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(reporting.router, prefix="/reporting", tags=["reporting"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])
