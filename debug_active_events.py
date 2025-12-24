#!/usr/bin/env python3
import asyncio
import json
import httpx

async def check_active_events():
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Checking active events/markets...\n")
        
        # Try different endpoints for active markets
        endpoints = [
            "/events",
            "/events?active=true",
            "/markets?active=true",
            "/active-markets",
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    print(f"✅ GET {endpoint} - {response.status_code}")
                    data = response.json()
                    
                    print(f"   Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"   Count: {len(data)}")
                        if data:
                            first = data[0]
                            if isinstance(first, dict):
                                print(f"   First item keys: {list(first.keys())}")
                                print(f"\n   First item (sample):")
                                item_json = json.dumps(first, indent=2, default=str)
                                lines = item_json.split("\n")[:30]
                                for line in lines:
                                    print(f"   {line}")
                                if len(item_json.split("\n")) > 30:
                                    print("   ...")
                    elif isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())[:15]}")
                    
                    print("\n" + "="*80 + "\n")
                    break
                else:
                    print(f"❌ GET {endpoint} - {response.status_code}")
            except Exception as e:
                print(f"❌ GET {endpoint} - Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_active_events())