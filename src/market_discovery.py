"""Market discovery - find best markets by criteria (based on find_best_markets.py)"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class MarketDiscovery:
    """Find best markets matching criteria"""
    
    def __init__(self, api_url: str = "https://gamma-api.polymarket.com"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def find_best_market(
        self,
        min_volume_24h: float = 10000,
        max_spread_bps: int = 500,
    ) -> dict[str, Any] | None:
        """
        Find the best (highest volume) active market matching criteria.
        Uses EXACT logic from find_best_markets.py
        
        Returns:
            Market dict with id, question, volume_24h, spread_bps, etc.
            or None if no market found
        """
        try:
            # ТОЧНО КАК В СКРИПТЕ: используем query params
            response = await self.client.get(
                f"{self.api_url}/markets",
                params={"active": "true", "closed": "false"}
            )
            response.raise_for_status()
            
            markets = response.json()
            
            if not isinstance(markets, list):
                logger.error("invalid_markets_response", response_type=type(markets))
                return None
            
            logger.debug("markets_fetched", total_count=len(markets))
            
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
                
                # Calculate spread in bps - ТОЧНО КАК В СКРИПТЕ
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
                logger.warning(
                    "no_candidates_found",
                    total_markets=len(markets),
                )
                return None
            
            # Filter by criteria - ТОЧНО КАК В СКРИПТЕ
            filtered = [
                m for m in candidates 
                if m['volume_24h'] >= min_volume_24h and m['spread_bps'] <= max_spread_bps
            ]
            
            if not filtered:
                logger.warning(
                    "no_markets_match_criteria",
                    min_volume=min_volume_24h,
                    max_spread=max_spread_bps,
                    num_candidates=len(candidates),
                )
                return None
            
            # Sort by volume
            filtered.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            # Вернуть несколько рынков для выбора
            return {
                "candidates": filtered[:10],  # Top 10 markets
                "selected": filtered[0],  # Default: best one
            }
            
        except Exception as e:
            logger.error("market_discovery_failed", error=str(e), exc_info=True)
            return None
    
    async def interactive_market_selection(
        self,
        min_volume_24h: float = 10000,
        max_spread_bps: int = 500,
    ) -> str | None:
        """
        Find markets and ask user to select one interactively.
        
        Returns:
            Selected market ID or None if cancelled
        """
        try:
            # Получить рынки
            response = await self.client.get(
                f"{self.api_url}/markets",
                params={"active": "true", "closed": "false"}
            )
            response.raise_for_status()
            
            markets = response.json()
            
            if not isinstance(markets, list):
                logger.error("invalid_markets_response", response_type=type(markets))
                return None
            
            candidates = []
            
            for market in markets:
                if not isinstance(market, dict):
                    continue
                
                active = market.get('active', False)
                closed = market.get('closed', False)
                
                if not active or closed:
                    continue
                
                best_bid = float(market.get('bestBid', 0))
                best_ask = float(market.get('bestAsk', 1))
                volume_24h = float(market.get('volume24hr', 0) or 0)
                
                if volume_24h < 100:
                    continue
                
                if best_bid > 0 and best_ask > 0 and best_ask > best_bid:
                    spread_bps = int((best_ask - best_bid) / ((best_bid + best_ask) / 2) * 10000)
                else:
                    spread_bps = 10000
                
                if volume_24h >= min_volume_24h and spread_bps <= max_spread_bps:
                    candidates.append({
                        'id': market.get('id'),
                        'question': market.get('question', '')[:70],
                        'volume_24h': volume_24h,
                        'liquidity': float(market.get('liquidity', 0) or 0),
                        'spread_bps': spread_bps,
                        'bid': best_bid,
                        'ask': best_ask,
                    })
            
            if not candidates:
                logger.error("no_markets_found")
                print("\n❌ No markets found matching criteria")
                return None
            
            # Sort by volume
            candidates.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            # Display selection menu
            print("\n" + "="*120)
            print("🎯 SELECT A MARKET TO TRADE")
            print("="*120 + "\n")
            
            for i, m in enumerate(candidates[:15], 1):
                print(f"{i:2d}. Market ID: {m['id']}")
                print(f"    Question: {m['question']}")
                print(f"    Volume 24h: ${m['volume_24h']:,.2f}")
                print(f"    Liquidity: ${m['liquidity']:,.2f}")
                print(f"    Spread: {m['spread_bps']} bps")
                print(f"    Bid/Ask: {m['bid']:.6f} / {m['ask']:.6f}")
                print()
            
            print("="*120)
            
            # Get user input
            while True:
                try:
                    choice = input("Enter market number (or 'q' to quit): ").strip()
                    
                    if choice.lower() == 'q':
                        logger.info("market_selection_cancelled")
                        return None
                    
                    idx = int(choice) - 1
                    if 0 <= idx < len(candidates):
                        selected = candidates[idx]
                        logger.info(
                            "market_selected",
                            market_id=selected['id'],
                            question=selected['question'],
                            volume_24h=selected['volume_24h'],
                            spread_bps=selected['spread_bps'],
                        )
                        print(f"\n✅ Selected: {selected['id']}")
                        print(f"   {selected['question']}")
                        print(f"   Volume: ${selected['volume_24h']:,.2f}")
                        print(f"   Spread: {selected['spread_bps']} bps\n")
                        return selected['id']
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(candidates)}")
                except ValueError:
                    print("❌ Invalid input. Please enter a number or 'q'")
                    
        except Exception as e:
            logger.error("interactive_selection_failed", error=str(e), exc_info=True)
            return None
    
    async def close(self):
        await self.client.aclose()