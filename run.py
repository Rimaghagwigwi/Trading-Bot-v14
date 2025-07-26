#!/usr/bin/env python3
"""
Crypto Trading Bot Launch Script
"""

import os
import sys
from backend.app import create_app

def main():
    """Main entry point"""
    # Create the Flask application
    app = create_app()
    
    # Local development configuration
    if __name__ == "__main__":
        print("🚀 Launching the Crypto Trading Bot...")
        print("📊 Backtest interface available at: http://localhost:5000")
        print("⚠️  Development mode - Local use only")
        
        # Start the Flask server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )

if __name__ == "__main__":
    main()