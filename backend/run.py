#!/usr/bin/env python3
"""
Script per avviare il backend FastAPI
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Avvio Taboolo Backend...")
    print("📍 API disponibile su: http://localhost:8000")
    print("📚 Documentazione Swagger: http://localhost:8000/docs")
    print("🔄 Ricaricamento automatico attivo\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )
