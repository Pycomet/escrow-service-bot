import logging
import random
import os
from datetime import datetime
from typing import Dict, List, Optional

import google.generativeai as genai
import requests

from config import TRADING_CHANNEL, CONTACT_SUPPORT

logger = logging.getLogger(__name__)

# Configure Gemini API
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        logger.warning("GEMINI_API_KEY not set. AI content generation disabled.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")


class MarketDataFetcher:
    """Fetches cryptocurrency market data from CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.supported_coins = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH', 
            'tether': 'USDT',
            'litecoin': 'LTC',
            'dogecoin': 'DOGE',
            'binancecoin': 'BNB',
            'solana': 'SOL',
            'tron': 'TRX'
        }
    
    async def get_market_data(self) -> Dict:
        """Fetch current market data for supported cryptocurrencies"""
        try:
            # Get price data for all supported coins
            coin_ids = ','.join(self.supported_coins.keys())
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_ids,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            raw_data = response.json()
            
            return self._format_market_data(raw_data)
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return self._get_fallback_data()
    
    def _format_market_data(self, raw_data: Dict) -> Dict:
        """Format raw CoinGecko data for use in content generation"""
        formatted = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime('%B %d, %Y'),
            'prices': {},
            'changes': {},
            'market_sentiment': 'neutral'
        }
        
        total_change = 0
        valid_changes = 0
        
        for coin_id, symbol in self.supported_coins.items():
            if coin_id in raw_data:
                price = raw_data[coin_id].get('usd', 0)
                change = raw_data[coin_id].get('usd_24h_change', 0)
                
                formatted['prices'][symbol] = price
                formatted['changes'][symbol] = change
                
                if change is not None:
                    total_change += change
                    valid_changes += 1
        
        # Calculate overall market sentiment
        if valid_changes > 0:
            avg_change = total_change / valid_changes
            if avg_change > 2:
                formatted['market_sentiment'] = 'bullish'
            elif avg_change < -2:
                formatted['market_sentiment'] = 'bearish'
            else:
                formatted['market_sentiment'] = 'neutral'
        
        return formatted
    
    def _get_fallback_data(self) -> Dict:
        """Provide fallback data when API is unavailable"""
        return {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime('%B %d, %Y'),
            'prices': {
                'BTC': 43000,
                'ETH': 2500,
                'USDT': 1.000,
                'LTC': 70,
                'DOGE': 0.08
            },
            'changes': {
                'BTC': 0.5,
                'ETH': -1.2,
                'USDT': 0.0,
                'LTC': 2.1,
                'DOGE': 5.3
            },
            'market_sentiment': 'neutral'
        }


class ContentPromptTemplates:
    """Contains all prompt templates for AI content generation"""
    
    EDUCATIONAL_PROMPTS = {
        "trading_basics": {
            "prompt": """Create a concise, professional educational post about {topic} for a crypto P2P trading community.

Guidelines:
- Keep it under 200 words
- Include 2-3 actionable tips
- Use emojis appropriately (🔐💡✅⚠️)
- End with relevant hashtags
- Focus on safety and best practices
- Write in a community-focused, helpful tone
- Mention our escrow platform's security benefits naturally

Topic: {topic}""",
            
            "topics": [
                "verifying trader reputation before starting trades",
                "understanding escrow protection in P2P trading", 
                "recognizing common crypto trading scams",
                "calculating fair exchange rates",
                "timing your crypto trades effectively",
                "managing trading risks in volatile markets",
                "understanding transaction fees and gas costs",
                "choosing the right cryptocurrency for P2P trades",
                "secure communication during trades",
                "best practices for first-time crypto traders"
            ]
        },
        
        "security_focus": {
            "prompt": """Generate a security-focused educational post for crypto traders.

Requirements:
- Focus on {security_aspect}
- Include specific warning signs or red flags
- Provide 3 concrete steps users can take
- Use security-related emojis (🔐🛡️⚠️🚨)
- Keep tone serious but accessible
- End with security-related hashtags
- Mention how our escrow service provides protection

Security aspect: {security_aspect}""",
            
            "topics": [
                "protecting private keys and wallet security",
                "identifying fake escrow services",
                "secure communication during trades", 
                "avoiding social engineering attacks",
                "verifying payment confirmations",
                "safe practices for large trades",
                "recognizing phishing attempts",
                "two-factor authentication importance"
            ]
        }
    }
    
    MARKET_ANALYSIS_PROMPTS = {
        "daily_brief": {
            "prompt": """Create a professional daily crypto market brief for P2P traders.

Use this market data: {market_data}

Structure:
- Start with "🌅 **Crypto Market Brief - {date}**"
- Include price movements for BTC, ETH, USDT with change percentages
- Add 2-3 sentences about market sentiment
- Mention which coins might be good for P2P trading today
- Include trading advice based on current conditions
- End with relevant hashtags (#CryptoMarket #P2PTrading #Bitcoin #Ethereum)
- Keep under 150 words
- Professional but accessible tone
- Encourage using our secure escrow platform""",
        },
        
        "weekly_analysis": {
            "prompt": """Generate a weekly crypto market analysis for P2P traders.

Market data: {market_data}
Week period: {date_range}

Include:
- Weekly performance summary for major cryptos
- Key events that affected prices this week
- Outlook for P2P trading opportunities
- Risk assessment for the coming week
- 2-3 specific trading recommendations
- Use 📊📈📉 emojis appropriately
- Professional analysis tone
- End with market-focused hashtags
- Mention our platform's security benefits"""
        }
    }
    
    PLATFORM_PROMPTS = {
        "feature_highlight": {
            "prompt": """Create a professional post highlighting a platform feature for our escrow service.

Feature to highlight: {feature}

Requirements:
- Explain the feature's benefit to users
- Use 2-3 bullet points for clarity
- Include trust-building language
- Mention security/safety benefits
- Use professional emojis (✅🔧🛡️⚙️)
- Keep tone confident but not boastful
- End with platform-related hashtags
- Under 180 words
- Include call-to-action to try the platform

Feature: {feature}""",
            
            "features": [
                "multi-signature wallet security system",
                "verified broker network", 
                "automated escrow release process",
                "real-time transaction monitoring",
                "comprehensive dispute resolution",
                "multi-currency support across 8+ coins",
                "gas fee optimization for Ethereum trades",
                "24/7 platform availability and support",
                "encrypted communication system",
                "advanced fraud detection algorithms"
            ]
        },
        
        "trust_building": {
            "prompt": """Generate a trust-building post about our escrow platform's reliability.

Focus area: {trust_aspect}

Guidelines:
- Emphasize security and user protection
- Include specific measures we implement
- Use confidence-building language
- Avoid overpromising or exaggerating
- Include relevant emojis (🛡️✅🔐💎)
- Professional, trustworthy tone
- End with trust-related hashtags
- Mention our community channels: @{trading_channel}
- Include subtle call-to-action

Trust aspect: {trust_aspect}""",
            
            "aspects": [
                "how our escrow system protects both buyers and sellers",
                "the rigorous verification process for platform brokers",
                "security measures protecting user funds",
                "transparency in fee structure and processes", 
                "customer support and dispute resolution efficiency",
                "platform uptime and reliability statistics",
                "user fund insurance and protection policies"
            ]
        }
    }


class AIContentGenerator:
    """Main class for generating AI-powered community content"""
    
    def __init__(self):
        self.market_fetcher = MarketDataFetcher()
        self.templates = ContentPromptTemplates()
        self.model_name = "gemini-2.5-flash"
    
    async def generate_content(self, content_type: str, **kwargs) -> Optional[str]:
        """Generate content based on type and parameters"""
        try:
            if content_type == "market_brief":
                return await self._generate_market_brief()
            elif content_type == "educational":
                return await self._generate_educational_content()
            elif content_type == "platform_update":
                return await self._generate_platform_content()
            elif content_type == "security_tip":
                return await self._generate_security_content()
            elif content_type == "weekly_analysis":
                return await self._generate_weekly_analysis()
            else:
                logger.error(f"Unknown content type: {content_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating {content_type} content: {e}")
            return self._get_fallback_content(content_type)
    
    async def _generate_market_brief(self) -> str:
        """Generate daily market brief"""
        market_data = await self.market_fetcher.get_market_data()
        
        # Format market data for prompt
        formatted_data = f"""
        BTC: ${market_data['prices']['BTC']:,.0f} ({market_data['changes']['BTC']:+.1f}% 24h)
        ETH: ${market_data['prices']['ETH']:,.0f} ({market_data['changes']['ETH']:+.1f}% 24h)
        USDT: ${market_data['prices']['USDT']:.3f} ({market_data['changes']['USDT']:+.1f}% 24h)
        Market Sentiment: {market_data['market_sentiment']}
        """
        
        prompt = self.templates.MARKET_ANALYSIS_PROMPTS["daily_brief"]["prompt"].format(
            market_data=formatted_data,
            date=market_data['date']
        )
        
        return await self._call_gemini_api(prompt)
    
    async def _generate_educational_content(self) -> str:
        """Generate educational content"""
        # Randomly select a category and topic
        category = random.choice(list(self.templates.EDUCATIONAL_PROMPTS.keys()))
        topic = random.choice(self.templates.EDUCATIONAL_PROMPTS[category]["topics"])
        
        prompt = self.templates.EDUCATIONAL_PROMPTS[category]["prompt"].format(topic=topic)
        
        return await self._call_gemini_api(prompt)
    
    async def _generate_platform_content(self) -> str:
        """Generate platform feature highlight"""
        feature = random.choice(self.templates.PLATFORM_PROMPTS["feature_highlight"]["features"])
        
        prompt = self.templates.PLATFORM_PROMPTS["feature_highlight"]["prompt"].format(feature=feature)
        
        return await self._call_gemini_api(prompt)
    
    async def _generate_security_content(self) -> str:
        """Generate security-focused content"""
        topic = random.choice(self.templates.EDUCATIONAL_PROMPTS["security_focus"]["topics"])
        
        prompt = self.templates.EDUCATIONAL_PROMPTS["security_focus"]["prompt"].format(
            security_aspect=topic
        )
        
        return await self._call_gemini_api(prompt)
    
    async def _generate_weekly_analysis(self) -> str:
        """Generate weekly market analysis"""
        market_data = await self.market_fetcher.get_market_data()
        
        # Create date range for the week
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
        
        formatted_data = f"""
        Weekly Performance:
        BTC: ${market_data['prices']['BTC']:,.0f} ({market_data['changes']['BTC']:+.1f}% 24h)
        ETH: ${market_data['prices']['ETH']:,.0f} ({market_data['changes']['ETH']:+.1f}% 24h)
        Overall Sentiment: {market_data['market_sentiment']}
        """
        
        prompt = self.templates.MARKET_ANALYSIS_PROMPTS["weekly_analysis"]["prompt"].format(
            market_data=formatted_data,
            date_range=date_range
        )
        
        return await self._call_gemini_api(prompt)
    
    async def _call_gemini_api(self, prompt: str) -> str:
        """Make API call to Gemini"""
        try:
            if not GEMINI_API_KEY:
                raise ValueError("Gemini API key not configured")
            
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                raise ValueError("Empty response from Gemini API")
                
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _get_fallback_content(self, content_type: str) -> str:
        """Provide fallback content when AI generation fails"""
        fallback_content = {
            "market_brief": """🌅 **Crypto Market Brief**

₿ BTC: Market showing steady activity
Ξ ETH: Ethereum network performing well  
₮ USDT: Stable as expected

📊 Perfect time for secure P2P trading!
Use our escrow service for safe transactions.

#CryptoMarket #P2PTrading #EscrowSafety""",

            "educational": """💡 **Trading Tip**

Always verify your trading partner's reputation:
✅ Check completed trade history
✅ Read user reviews and ratings  
✅ Start with smaller amounts

Our escrow system protects both parties throughout the entire process.

#TradingSafety #CryptoTips #EscrowProtection""",

            "platform_update": """🔧 **Platform Update**

Our security systems continue to protect your trades:
✅ Multi-signature wallet protection
✅ Real-time fraud monitoring
✅ Verified broker network

Trade with confidence on our secure platform.

#PlatformSecurity #EscrowSafety""",

            "security_tip": """🔐 **Security Reminder**

Protect your crypto assets:
⚠️ Never share private keys
⚠️ Verify all transaction details
⚠️ Use trusted escrow services only

Our platform provides bank-level security for all trades.

#CryptoSecurity #SafeTrading"""
        }
        
        return fallback_content.get(content_type, "Content temporarily unavailable.")
