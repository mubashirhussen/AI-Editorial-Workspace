#!/usr/bin/env python3
"""
Cryptographic Secret Generation Utility.
Generates production-grade JWT_SECRET and AES-128 Fernet ENCRYPTION_KEY.
Usage: python scripts/generate_secrets.py
"""

import secrets
import base64
from cryptography.fernet import Fernet

def generate_production_secrets():
    jwt_secret = secrets.token_hex(32)
    encryption_key = Fernet.generate_key().decode("utf-8")
    
    print("=" * 60)
    print("PRODUCTION SECRETS GENERATED (DO NOT COMMIT TO GIT)")
    print("=" * 60)
    print(f"SECRET_KEY={jwt_secret}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print("=" * 60)
    print("Copy these values into your production environment or secret manager.")
    return {"SECRET_KEY": jwt_secret, "ENCRYPTION_KEY": encryption_key}

if __name__ == "__main__":
    generate_production_secrets()

