#!/usr/bin/env python3
"""Debug script to check ALL markets and their criteria"""

import asyncio
import httpx


async def check_all_markets():
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "="*140)
        print("🔍 CHECKING ALL ACTIVE MARKETS")
        print("="*140 + "\n")
        
        response = await client.get(
            f"{base_url}/markets",
            params={"active": "true", "closed": "false"}
        )
        markets = response.json()
        
        print(f"Total markets: {len(markets)}\n")
        
        all_markets = []
        
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
            
            # Calculate spread
            if best_bid > 0 and best_ask > 0 and best_ask > best_bid:
                spread_bps = int((best_ask - best_bid) / ((best_bid + best_ask) / 2) * 10000)
            else:
                spread_bps = 10000
            
            all_markets.append({
                'id': market_id,
                'question': question[:60],
                'volume_24h': volume_24h,
                'liquidity': liquidity,
                'spread_bps': spread_bps,
                'bid': best_bid,
                'ask': best_ask,
                'active': active,
                'closed': closed,
            })
        
        # Sort by volume
        all_markets.sort(key=lambda x: x['volume_24h'], reverse=True)
        
        print(f"{'#':<3} {'Market ID':<12} {'Volume 24h':<15} {'Spread (bps)':<15} Question")
        print("-"*140)
        
        for i, m in enumerate(all_markets, 1):
            vol_str = f"${m['volume_24h']:,.0f}"
            print(f"{i:<3} {m['id']:<12} {vol_str:<15} {m['spread_bps']:<15} {m['question']}")
        
        print("\n" + "="*140)
        print("📊 ANALYSIS")
        print("="*140)
        
        # Current criteria
        min_vol = 10000
        max_spread = 500
        
        matching = [m for m in all_markets if m['volume_24h'] >= min_vol and m['spread_bps'] <= max_spread]
        print(f"\nWith current criteria (volume >= ${min_vol:,}, spread <= {max_spread} bps):")
        print(f"  ✓ Matching markets: {len(matching)}")
        
        # Try lower criteria
        matching_lower = [m for m in all_markets if m['volume_24h'] >= 1000 and m['spread_bps'] <= 1000]
        print(f"\nWith lower criteria (volume >= $1,000, spread <= 1000 bps):")
        print(f"  ✓ Matching markets: {len(matching_lower)}")
        
        # Try even lower
        matching_very_low = [m for m in all_markets if m['volume_24h'] >= 100 and m['spread_bps'] <= 5000]
        print(f"\nWith very low criteria (volume >= $100, spread <= 5000 bps):")
        print(f"  ✓ Matching markets: {len(matching_very_low)}")
        
        print("\n" + "="*140)
        print("💡 RECOMMENDATIONS")
        print("="*140)
        print(f"\nTo get more markets, try these criteria in .env:\n")
        print(f"  Option 1 (Medium): MIN_VOLUME_24H=1000, MAX_SPREAD_BPS=1000")
        print(f"  Option 2 (Relaxed): MIN_VOLUME_24H=100, MAX_SPREAD_BPS=5000")
        print(f"  Option 3 (No filter): MIN_VOLUME_24H=0, MAX_SPREAD_BPS=100000\n")
        
        print("="*140 + "\n")


if __name__ == "__main__":
    asyncio.run(check_all_markets())