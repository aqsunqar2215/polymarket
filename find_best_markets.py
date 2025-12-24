#!/usr/bin/env python3
"""Find best markets by volume and spread"""

import asyncio
import httpx


async def find_best_markets(
    min_volume_24h: float = 10000,
    max_spread_bps: int = 500,
    limit: int = 15,
):
    """Find best markets by criteria"""
    
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "="*100)
        print(f"🔍 Searching for active markets...")
        print(f"   Min Volume 24h: ${min_volume_24h:,.0f}")
        print(f"   Max Spread: {max_spread_bps} bps")
        print("="*100 + "\n")
        
        # Get markets with active=true and closed=false
        response = await client.get(
            f"{base_url}/markets",
            params={"active": "true", "closed": "false"}
        )
        markets = response.json()
        
        print(f"📊 Total active markets: {len(markets)}\n")
        
        candidates = []
        
        for market in markets:
            if not isinstance(market, dict):
                continue
            
            market_id = market.get('id')
            question = market.get('question', '')
            active = market.get('active', False)
            closed = market.get('closed', False)
            
            best_bid = float(market.get('bestBid', 0))
            best_ask = float(market.get('bestAsk', 1))
            volume_24h = float(market.get('volume24hr', 0) or 0)
            liquidity = float(market.get('liquidity', 0) or 0)
            
            # Calculate spread in bps
            if best_bid > 0 and best_ask > 0 and best_ask > best_bid:
                spread_bps = int((best_ask - best_bid) / ((best_bid + best_ask) / 2) * 10000)
            else:
                spread_bps = 10000
            
            # Only active and open markets
            if not active or closed:
                continue
            
            # Only if has some volume
            if volume_24h < 100:
                continue
            
            candidates.append({
                'id': market_id,
                'question': question[:70],
                'volume_24h': volume_24h,
                'liquidity': liquidity,
                'spread_bps': spread_bps,
                'bid': best_bid,
                'ask': best_ask,
            })
        
        if not candidates:
            print("❌ No active markets found\n")
            return
        
        # Filter by criteria
        filtered = [
            m for m in candidates 
            if m['volume_24h'] >= min_volume_24h and m['spread_bps'] <= max_spread_bps
        ]
        
        if filtered:
            print(f"✅ Found {len(filtered)} markets matching criteria:\n")
            filtered.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            for i, m in enumerate(filtered[:limit], 1):
                print(f"{i}. Market ID: {m['id']}")
                print(f"   Question: {m['question']}")
                print(f"   Volume 24h: ${m['volume_24h']:,.2f}")
                print(f"   Liquidity: ${m['liquidity']:,.2f}")
                print(f"   Spread: {m['spread_bps']} bps")
                print(f"   Bid/Ask: {m['bid']:.6f} / {m['ask']:.6f}")
                print()
            
            print("="*100)
            print(f"\n📌 RECOMMENDATION: Use Market ID {filtered[0]['id']}")
            print(f"   Add to .env: MARKET_ID={filtered[0]['id']}")
            print(f"   Volume: ${filtered[0]['volume_24h']:,.2f}")
            print(f"   Spread: {filtered[0]['spread_bps']} bps\n")
        else:
            # Show top markets by volume anyway
            print(f"⚠️  No markets match those criteria")
            print(f"📊 Showing top {min(limit, len(candidates))} markets by volume:\n")
            
            candidates.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            for i, m in enumerate(candidates[:limit], 1):
                print(f"{i}. Market ID: {m['id']}")
                print(f"   Question: {m['question']}")
                print(f"   Volume 24h: ${m['volume_24h']:,.2f}")
                print(f"   Liquidity: ${m['liquidity']:,.2f}")
                print(f"   Spread: {m['spread_bps']} bps")
                print(f"   Bid/Ask: {m['bid']:.6f} / {m['ask']:.6f}")
                print()
            
            print("="*100)
            print(f"\n💡 Suggestion: Market ID {candidates[0]['id']}")
            print(f"   Highest volume: ${candidates[0]['volume_24h']:,.2f}")
            print(f"   Spread: {candidates[0]['spread_bps']} bps\n")


if __name__ == "__main__":
    import sys
    
    min_volume = 10000
    max_spread = 500
    limit = 15
    
    print("""
╔════════════════════════════════════════════════════════════╗
║         🚀 POLYMARKET BEST MARKETS FINDER 🚀              ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        min_volume = float(sys.argv[1])
    if len(sys.argv) > 2:
        max_spread = int(sys.argv[2])
    if len(sys.argv) > 3:
        limit = int(sys.argv[3])
    
    asyncio.run(find_best_markets(min_volume, max_spread, limit))