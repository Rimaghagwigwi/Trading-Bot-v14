#!/usr/bin/env python3
"""
Script de lancement du Bot de Trading Crypto
"""

import os
import sys
from backend.app import create_app

def main():
    """Point d'entrée principal"""
    # Création de l'application Flask
    app = create_app()
    
    # Configuration pour le développement local
    if __name__ == "__main__":
        print("🚀 Lancement du Bot de Trading Crypto...")
        print("📊 Interface backtest disponible sur: http://localhost:5000")
        print("⚠️  Mode développement - Usage local uniquement")
        
        # Lancement du serveur Flask
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )

if __name__ == "__main__":
    main()