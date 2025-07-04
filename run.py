#!/usr/bin/env python3
"""
Point d'entrée pour l'application
Usage: python run.py
"""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
