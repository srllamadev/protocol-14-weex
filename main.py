"""
WEEX AI Trading Hackathon - Main Entry Point
=============================================
Author: Protocol-14 Team
Date: January 2026

This script initializes the WEEX API client and tests connectivity.
"""

import sys
from weex_client import WeexClient


def print_banner():
    """Print welcome banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║           🤖 WEEX AI TRADING HACKATHON 🤖                    ║
    ║                    Protocol-14 Team                          ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  🔐 Secure API Connection with HMAC SHA256 Authentication    ║
    ║  📊 Ready for Algo-Trading Tasks                             ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point"""
    print_banner()
    
    try:
        # Initialize WEEX Client (loads credentials from .env)
        print("🚀 Initializing WEEX Client...")
        client = WeexClient()
        
        # Test API connectivity
        if client.test_connectivity():
            print("🎉 API Connection Verified! Ready for trading tasks.")
            
            # Show account info
            print("\n📊 ACCOUNT SUMMARY")
            print("-" * 40)
            try:
                account = client.get_account_assets()
                if isinstance(account, list) and len(account) > 0:
                    for acc in account:
                        print(f"   💰 Coin: {acc.get('coinName', 'N/A')}")
                        print(f"   💵 Available: {acc.get('available', 'N/A')}")
                        print(f"   🔒 Frozen: {acc.get('frozen', 'N/A')}")
                        print(f"   📈 Equity: {acc.get('equity', 'N/A')}")
                        print("-" * 40)
                else:
                    print(f"   📊 Response: {account}")
            except Exception as e:
                print(f"   ⚠️ Could not fetch account details: {e}")
            
            return 0
        else:
            print("❌ API Connection Failed. Please check your credentials.")
            return 1
            
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Make sure your .env file contains:")
        print("   WEEX_API_KEY=your_api_key")
        print("   WEEX_SECRET_KEY=your_secret_key")
        print("   WEEX_PASSPHRASE=your_passphrase")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
