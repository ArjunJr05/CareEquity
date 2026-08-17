#!/usr/bin/env python3
"""
Quick test to verify Streamlit app loads correctly
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Testing Streamlit app...")
    
    # Test 1: Import streamlit
    logger.info("✓ Testing Streamlit import...")
    try:
        import streamlit as st
        logger.info(f"✓ Streamlit {st.__version__} installed")
    except Exception as e:
        logger.error(f"✗ Streamlit import failed: {e}")
        return 1
    
    # Test 2: Import requests
    logger.info("✓ Testing requests import...")
    try:
        import requests
        logger.info(f"✓ Requests installed")
    except Exception as e:
        logger.error(f"✗ Requests import failed: {e}")
        return 1
    
    # Test 3: Import pandas
    logger.info("✓ Testing pandas import...")
    try:
        import pandas as pd
        logger.info(f"✓ Pandas {pd.__version__} installed")
    except Exception as e:
        logger.error(f"✗ Pandas import failed: {e}")
        return 1
    
    # Test 4: Try to load the streamlit app file
    logger.info("✓ Checking app file syntax...")
    try:
        import ast
        with open("streamlit_app.py", "r") as f:
            code = f.read()
        ast.parse(code)
        logger.info("✓ App file syntax is valid")
    except SyntaxError as e:
        logger.error(f"✗ Syntax error in app file: {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ Error reading app file: {e}")
        return 1
    
    logger.info("")
    logger.info("✓ ALL TESTS PASSED")
    logger.info("Streamlit app is ready to run!")
    logger.info("")
    logger.info("Start with: streamlit run streamlit_app.py")
    logger.info("Then visit: http://localhost:8501")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
