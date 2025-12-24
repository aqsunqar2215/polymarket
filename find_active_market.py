#!/usr/bin/env python3
import asyncio
import httpx

async def find_active_market():
    base_url = "https://gamma-api.polymarket.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Searching for active, open markets with real data...\n")
        
        # Get events directly
        response = await client.get(f"{base_url}/events")
        events = response.json()
        
        print(f"Total events: {len(events)}\n")
        
        candidates = []
        
        for event in events:
            if isinstance(event, dict) and 'markets' in event:
                event_title = event.get('title', '')[:60]
                event_active = event.get('active')
                event_closed = event.get('closed')
                
                markets = event.get('markets', [])
                for market in markets:
                    if isinstance(market, dict):
                        market_id = market.get('id')
                        best_bid = float(market.get('bestBid', 0))
                        best_ask = float(market.get('bestAsk', 1))
                        active = market.get('active')
                        closed = market.get('closed')
                        question = market.get('question', '')[:80]
                        volume = float(market.get('volume', 0))
                        liquidity = float(market.get('liquidity', 0))
                        
                        # Print all markets with their status
                        status = "✅" if (active and not closed) else "❌"
                        has_data = "📊" if (0 < best_bid < best_ask < 1) else "⚠️"
                        
                        print(f"{status} {has_data} ID: {market_id:6s} | Bid: {best_bid:.4f} Ask: {best_ask:.4f} | Vol: ${volume:.2f} | Liq: ${liquidity:.2f}")
                        print(f"         Question: {question}")
                        print(f"         Event: {event_title}")
                        print()
                        
                        # Collect candidates
                        if active and not closed:
                            candidates.append({
                                'id': market_id,
                                'question': question,
                                'bid': best_bid,
                                'ask': best_ask,
                                'spread': best_ask - best_bid if best_ask > best_bid else 0,
                                'volume': volume,
                                'liquidity': liquidity,
                                'event': event_title,
                            })
        
        print("\n" + "="*80)
        if candidates:
            print(f"\n✅ Found {len(candidates)} active, open markets:\n")
            candidates.sort(key=lambda x: x['volume'], reverse=True)
            
            for i, m in enumerate(candidates[:10], 1):
                print(f"{i}. Market ID: {m['id']}")
                print(f"   Question: {m['question']}")
                print(f"   Bid: {m['bid']:.6f} | Ask: {m['ask']:.6f} | Spread: {m['spread']:.6f}")
                print(f"   Volume: ${m['volume']:.2f} | Liquidity: ${m['liquidity']:.2f}")
                print(f"   Event: {m['event']}\n")
            
            print(f"\n📌 Recommendation: Use Market ID {candidates[0]['id']}")
            print(f"   Add to .env: MARKET_ID={candidates[0]['id']}")
        else:
            print("\n❌ No active, open markets found")
            print("All events appear to be closed or inactive")

if __name__ == "__main__":
    asyncio.run(find_active_market())