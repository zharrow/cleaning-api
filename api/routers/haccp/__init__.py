"""
HACCP Routers Package
Organize all HACCP-related API endpoints
"""

from fastapi import APIRouter
from . import children, suppliers, products, batches, meals, temperatures, equipment, cleaning_haccp, non_compliances, documents, meal_children

# Create main HACCP router
router = APIRouter()

# Include all sub-routers
router.include_router(children.router, prefix="/children", tags=["HACCP - Children"])
router.include_router(suppliers.router, prefix="/suppliers", tags=["HACCP - Suppliers"])
router.include_router(products.router, prefix="/products", tags=["HACCP - Products"])
router.include_router(batches.router, prefix="/batches", tags=["HACCP - Batches"])
router.include_router(meals.router, prefix="/meals", tags=["HACCP - Meals"])
router.include_router(temperatures.router, prefix="/temperatures", tags=["HACCP - Temperatures"])
router.include_router(equipment.router, prefix="/equipment", tags=["HACCP - Equipment"])
router.include_router(cleaning_haccp.router, prefix="/cleaning", tags=["HACCP - Cleaning"])
router.include_router(non_compliances.router, prefix="/non-compliances", tags=["HACCP - Non-Compliances"])
router.include_router(documents.router, prefix="/documents", tags=["HACCP - Documents"])
router.include_router(meal_children.router, prefix="/meal-children", tags=["HACCP - Meal Children"])
