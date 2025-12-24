#!/usr/bin/env python3
import asyncio
import json
import httpx

async def check_orderbook():
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Finding active open market for orderbook test...\n")
        
        # Get events with markets
        response = await client.get(f"{base_url}/events")
        events = response.json()
        
        # Find first active, open market
        target_market = None
        for event in events:
            if isinstance(event, dict) and 'markets' in event:
                markets = event.get('markets', [])
                for market in markets:
                    if isinstance(market, dict) and market.get('active') and not market.get('closed'):
                        target_market = market
                        break
            if target_market:
                break
        
        if not target_market:
            print("❌ No active, open markets found")
            print("\nTrying with first active market (even if closed)...")
            for event in events:
                if isinstance(event, dict) and 'markets' in event:
                    markets = event.get('markets', [])
                    for market in markets:
                        if isinstance(market, dict) and market.get('active'):
                            target_market = market
                            break
                if target_market:
                    break
        
        if not target_market:
            print("❌ No active markets found at all")
            return
        
        market_id = target_market.get('id')
        print(f"✅ Found market: {market_id}")
        print(f"   Question: {target_market.get('question', '')[:80]}")
        print(f"   Active: {target_market.get('active')}")
        print(f"   Closed: {target_market.get('closed')}")
        print(f"\n   bestBid: {target_market.get('bestBid')}")
        print(f"   bestAsk: {target_market.get('bestAsk')}")
        
        print(f"\n\nTesting orderbook endpoints with market ID: {market_id}\n")
        
        # Try different orderbook endpoints
        endpoints = [
            f"/markets/{market_id}",
            f"/markets/{market_id}/orderbook",
            f"/orderbook?market={market_id}",
            f"/book?market={market_id}",
            f"/clob/orderbook?market={market_id}",
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    print(f"✅ GET {endpoint} - 200 OK")
                    data = response.json()
                    print(f"   Response type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())[:10]}")
                    print()
                    break
                else:
                    print(f"❌ GET {endpoint} - {response.status_code}")
            except Exception as e:
                print(f"❌ GET {endpoint} - Error: {str(e)[:50]}")

if __name__ == "__main__":
    asyncio.run(check_orderbook())