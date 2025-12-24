#!/usr/bin/env python3
import asyncio
import httpx

async def check_markets():
    base_url = "https://gamma-api.polymarket.com"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{base_url}/markets")
        markets = response.json()
        
        print(f"Total markets: {len(markets)}\n")
        print("Markets status:")
        print("=" * 100)
        
        for i, m in enumerate(markets):
            market_id = m.get('id')
            question = m.get('question', '')[:60]
            active = m.get('active', False)
            closed = m.get('closed', False)
            
            status = "✅ OPEN" if (active and not closed) else "❌ CLOSED" if closed else "⏸️  INACTIVE"
            print(f"{i:2d}. ID: {market_id:5s} | Active: {active} | Closed: {closed} | {status} | Q: {question}")
        
        # Find open markets
        open_markets = [m for m in markets if m.get('active') and not m.get('closed')]
        print(f"\n\n📊 Open and active markets: {len(open_markets)}")
        
        if open_markets:
            for m in open_markets:
                print(f"  - ID: {m.get('id')} | {m.get('question', '')[:80]}")

if __name__ == "__main__":
    asyncio.run(check_markets())