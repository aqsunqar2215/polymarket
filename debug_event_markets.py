#!/usr/bin/env python3
import asyncio
import json
import httpx

async def check_event_markets():
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Checking event structure with markets...\n")
        
        response = await client.get(f"{base_url}/events")
        data = response.json()
        
        if data and isinstance(data, list):
            first_event = data[0]
            
            print(f"Event ID: {first_event.get('id')}")
            print(f"Event Title: {first_event.get('title')[:80]}")
            print(f"Active: {first_event.get('active')}")
            print(f"Closed: {first_event.get('closed')}")
            print(f"Has markets key: {'markets' in first_event}")
            
            if 'markets' in first_event:
                markets = first_event.get('markets', [])
                print(f"\nMarkets in event: {len(markets)}")
                
                if markets and isinstance(markets, list):
                    first_market = markets[0]
                    print(f"\nFirst market type: {type(first_market)}")
                    if isinstance(first_market, dict):
                        print(f"First market keys: {list(first_market.keys())}")
                        print(f"\nFirst market (sample):")
                        market_json = json.dumps(first_market, indent=2, default=str)
                        lines = market_json.split("\n")[:40]
                        for line in lines:
                            print(f"   {line}")
                        if len(market_json.split("\n")) > 40:
                            print("   ...")
                    elif isinstance(first_market, str):
                        print(f"First market (string): {first_market}")
            
            # Also check if we can get market by condition ID
            print("\n" + "="*80)
            print("\nLooking for conditionId or market reference...")
            
            market_keys_to_check = [k for k in first_event.keys() if 'market' in k.lower() or 'condition' in k.lower()]
            print(f"Keys with 'market' or 'condition': {market_keys_to_check}")

if __name__ == "__main__":
    asyncio.run(check_event_markets())