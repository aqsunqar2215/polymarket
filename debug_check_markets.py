#!/usr/bin/env python3
"""Debug script to check all markets and their criteria"""

import asyncio
from src.market_discovery import MarketDiscovery


async def main():
    discovery = MarketDiscovery()
    
    print("\n" + "="*120)
    print("🔍 CHECKING ALL MARKETS")
    print("="*120 + "\n")
    
    markets = await discovery.debug_list_all_markets()
    
    print(f"{'#':<3} {'Market ID':<12} {'Volume 24h':<15} {'Spread (bps)':<15} {'Status':<12} Question")
    print("-"*120)
    
    for i, m in enumerate(markets, 1):
        print(
            f"{i:<3} {m['id']:<12} ${m['volume_24h']:<14,.0f} {m['spread_bps']:<15} {m['status']:<12} {m['question']}"
        )
    
    print("\n" + "="*120)
    print("📊 SUMMARY")
    print("="*120)
    print(f"Total markets: {len(markets)}")
    
    # Show which ones match criteria
    min_volume = 10000
    max_spread = 500
    
    matching = [m for m in markets if m['volume_24h'] >= min_volume and m['spread_bps'] <= max_spread]
    print(f"Matching (volume >= ${min_volume}, spread <= {max_spread} bps): {len(matching)}")
    
    if matching:
        print("\n✅ Matching markets:")
        for m in matching[:5]:
            print(f"  - {m['id']}: Volume ${m['volume_24h']:,.0f}, Spread {m['spread_bps']} bps")
    else:
        print("\n❌ No markets match criteria")
        print("\n💡 Recommendation: Lower your criteria")
        print(f"   Top market by volume: {markets[0]['id']} (${markets[0]['volume_24h']:,.0f}, {markets[0]['spread_bps']} bps)")
        print(f"   Min volume found: ${min(m['volume_24h'] for m in markets):,.0f}")
        print(f"   Max spread found: {max(m['spread_bps'] for m in markets)} bps")
    
    print("\n" + "="*120 + "\n")
    
    await discovery.close()


if __name__ == "__main__":
    asyncio.run(main())