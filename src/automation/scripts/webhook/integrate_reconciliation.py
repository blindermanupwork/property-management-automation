#!/usr/bin/env python3
"""
Script to integrate job reconciliation into the webhook handler.
This shows how to add the reconciliation capability to webhook.py
"""

import sys
from pathlib import Path

# Path to webhook.py
webhook_file = Path(__file__).parent / "webhook.py"

# Integration code to add after the imports section
integration_import = """
# Import reconciliation module
try:
    from webhook_reconciliation import integrate_reconciliation
    RECONCILIATION_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Job reconciliation module not available")
    RECONCILIATION_AVAILABLE = False
"""

# Integration code to add after worker thread starts
integration_setup = """
# Enable job reconciliation (dev environment only for now)
if RECONCILIATION_AVAILABLE and environment == 'development':
    try:
        # Need to pass the module globals to access tables and functions
        import sys
        current_module = sys.modules[__name__]
        integrate_reconciliation(current_module)
        logger.info("✅ Job reconciliation enabled for dev environment")
    except Exception as e:
        logger.error(f"❌ Failed to enable job reconciliation: {e}")
"""

def show_integration_instructions():
    """Show manual integration instructions"""
    print("=" * 60)
    print("WEBHOOK JOB RECONCILIATION INTEGRATION INSTRUCTIONS")
    print("=" * 60)
    print()
    print("To integrate job reconciliation into the webhook handler:")
    print()
    print("1. Add this import after the other imports in webhook.py:")
    print("-" * 60)
    print(integration_import)
    print("-" * 60)
    print()
    print("2. Add this setup code after the worker thread starts (around line 245):")
    print("-" * 60)
    print(integration_setup)
    print("-" * 60)
    print()
    print("3. The reconciliation will automatically:")
    print("   - Detect when webhooks arrive for jobs not linked to reservations")
    print("   - Match jobs to reservations based on property, time, and customer")
    print("   - Update Airtable with the matched job IDs")
    print("   - Only run in development environment (for safety)")
    print()
    print("4. To enable in production, change the condition:")
    print("   From: if RECONCILIATION_AVAILABLE and environment == 'development':")
    print("   To:   if RECONCILIATION_AVAILABLE:")
    print()
    print("5. Monitor logs for reconciliation activity:")
    print("   - Look for '🔍 No reservation linked to job' messages")
    print("   - Look for '🔄 Attempting to reconcile job' messages")
    print("   - Look for '✅ Successfully reconciled job' messages")
    print()
    print("Alternative: Use the standalone script for manual reconciliation:")
    print("   python3 /home/opc/automation/src/automation/scripts/hcp/reconcile-jobs-dev.py")
    print()

if __name__ == "__main__":
    show_integration_instructions()
    
    # Optional: Show the current webhook.py file info
    if webhook_file.exists():
        print(f"\nWebhook file location: {webhook_file}")
        print(f"File size: {webhook_file.stat().st_size:,} bytes")
        
        # Check if already integrated
        content = webhook_file.read_text()
        if "webhook_reconciliation" in content:
            print("\n⚠️  WARNING: Reconciliation may already be integrated!")
        else:
            print("\n✅ Webhook file is ready for integration")