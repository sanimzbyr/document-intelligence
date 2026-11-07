#!/usr/bin/env python3
"""
CLI utility to test and verify the configured LLM API connection.
Usage:
    python scripts/test_llm.py
"""
import sys
import os
import asyncio
import time

# Ensure backend package is in python path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "backend"))

from app.core.config import settings
from app.services.extraction_service import extraction_service


async def main():
    print("=" * 60)
    print("      AI DOCUMENT INTELLIGENCE - LLM VERIFICATION      ")
    print("=" * 60)
    
    provider, api_key, base_url, model = settings.get_llm_credentials()
    masked_key = (api_key[:6] + "..." + api_key[-4:]) if api_key and len(api_key) > 10 else "(none)"
    
    print(f"• Provider:  {provider}")
    print(f"• Model:     {model}")
    print(f"• Base URL:  {base_url}")
    print(f"• API Key:   {masked_key}")
    print("-" * 60)
    
    if not extraction_service.client:
        print("[!] Warning: No active LLM client configured.")
        print("    The system is currently running in fallback heuristic regex mode.")
        print("    Add GEMINI_API_KEY or GROQ_API_KEY to .env to enable AI extraction.")
        return 1

    print("[*] Testing live connection to LLM API...")
    start_time = time.time()
    try:
        sample_prompt = (
            "Invoice #TEST-456\n"
            "Date: 2026-04-01\n"
            "Vendor: Apex Supplies Inc.\n"
            "Customer: Nova Corp\n"
            "Item: Cloud Subscription x 1 = $100.00\n"
            "Subtotal: $100.00\n"
            "Tax: $10.00\n"
            "Total: $110.00 USD"
        )
        
        result = await extraction_service.extract_information(sample_prompt)
        elapsed = time.time() - start_time
        
        print(f"[✓] SUCCESS! Response received in {elapsed:.2f} seconds.")
        print("-" * 60)
        print("Extracted Invoice Data from LLM:")
        print(f"  • Invoice Number: {result.invoice_number}")
        print(f"  • Invoice Date:   {result.invoice_date}")
        print(f"  • Supplier Name:  {result.supplier_name}")
        print(f"  • Customer Name:  {result.customer_name}")
        print(f"  • Subtotal:       {result.subtotal}")
        print(f"  • Tax:            {result.tax}")
        print(f"  • Total:          {result.total} {result.currency}")
        print(f"  • Line Items:     {len(result.line_items)}")
        print(f"  • Confidence:     {result.confidence}")
        print("=" * 60)
        print("Your LLM API is online and fully functioning!")
        return 0
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[✗] FAILED after {elapsed:.2f} seconds.")
        print(f"    Error: {e}")
        print("-" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
