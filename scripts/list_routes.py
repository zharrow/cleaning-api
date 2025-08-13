#!/usr/bin/env python3
"""
Liste toutes les routes de l'API
"""
from api.main import app
from fastapi.routing import APIRoute

def list_routes():
    """Affiche toutes les routes de l'API"""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "methods": ", ".join(route.methods),
                "name": route.name,
                "tags": ", ".join(route.tags) if route.tags else ""
            })
    
    # Trier par path
    routes.sort(key=lambda x: x["path"])
    
    # Afficher
    print("\n📋 ROUTES DE L'API\n")
    print(f"{'Path':<40} {'Methods':<20} {'Name':<30} {'Tags':<20}")
    print("-" * 110)
    
    for route in routes:
        print(f"{route['path']:<40} {route['methods']:<20} {route['name']:<30} {route['tags']:<20}")
    
    print(f"\n✅ Total: {len(routes)} routes\n")

if __name__ == "__main__":
    list_routes()