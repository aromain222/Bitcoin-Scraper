#!/usr/bin/env python3
"""
Service Account Setup for Professional Scraping
"""

import requests
import time
import random
import json
import os
from typing import List, Dict, Optional

class ServiceAccountManager:
    def __init__(self):
        self.proxy_rotation = True
        self.user_agent_rotation = True
        self.rate_limiting = True
        
    def setup_proxy_service(self):
        """Setup proxy service recommendations"""
        
        print("🔧 SETTING UP PROFESSIONAL SCRAPING INFRASTRUCTURE")
        print("=" * 60)
        
        # 1. Proxy Services
        proxy_services = {
            "bright_data": {
                "url": "https://brightdata.com/",
                "cost": "$500/month",
                "features": ["Residential IPs", "99.9% success rate", "Unlimited bandwidth"],
                "best_for": "Enterprise scraping"
            },
            "smartproxy": {
                "url": "https://smartproxy.com/",
                "cost": "$75/month",
                "features": ["Residential & Datacenter IPs", "40M+ IPs", "Easy integration"],
                "best_for": "Professional scraping"
            },
            "oxylabs": {
                "url": "https://oxylabs.io/",
                "cost": "$300/month",
                "features": ["Residential IPs", "99.2% success rate", "Advanced targeting"],
                "best_for": "High-volume scraping"
            },
            "proxycrawl": {
                "url": "https://proxycrawl.com/",
                "cost": "$29/month",
                "features": ["Scraping API", "Built-in parsing", "Easy to use"],
                "best_for": "Quick setup"
            }
        }
        
        print("📋 RECOMMENDED PROXY SERVICES:")
        for service, details in proxy_services.items():
            print(f"\n🔹 {service.upper()}:")
            print(f"   💰 Cost: {details['cost']}")
            print(f"   🌟 Best for: {details['best_for']}")
            print(f"   ✨ Features: {', '.join(details['features'])}")
            print(f"   🔗 URL: {details['url']}")
        
        # 2. User Agent Services
        print(f"\n🤖 USER AGENT ROTATION SERVICES:")
        ua_services = {
            "fake_useragent": "Free Python library",
            "user_agents": "Free Python library", 
            "custom_rotation": "Build your own list"
        }
        
        for service, description in ua_services.items():
            print(f"   🔹 {service}: {description}")
        
        # 3. Rate Limiting Strategies
        print(f"\n⏱️ RATE LIMITING STRATEGIES:")
        rate_strategies = {
            "exponential_backoff": "Increase delays on failures",
            "random_jitter": "Add randomness to delays",
            "adaptive_limiting": "Adjust based on response times",
            "time_window": "Limit requests per time period"
        }
        
        for strategy, description in rate_strategies.items():
            print(f"   🔹 {strategy}: {description}")
        
        return proxy_services

class ProfessionalScraper:
    def __init__(self, proxy_config: Optional[Dict] = None):
        self.proxy_config = proxy_config or {}
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = 0
        
    def setup_proxy_rotation(self, proxy_list: List[str]):
        """Setup proxy rotation"""
        self.proxy_list = proxy_list
        self.current_proxy_index = 0
        
    def get_next_proxy(self):
        """Get next proxy from rotation"""
        if hasattr(self, 'proxy_list') and self.proxy_list:
            proxy = self.proxy_list[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            return {'http': proxy, 'https': proxy}
        return None
        
    def setup_user_agent_rotation(self):
        """Setup user agent rotation"""
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
    def get_random_user_agent(self):
        """Get random user agent"""
        if hasattr(self, 'user_agents'):
            return random.choice(self.user_agents)
        return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        
    def rate_limit(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last + random.uniform(0, max_delay - min_delay)
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def make_request(self, url: str, headers: Optional[Dict] = None, 
                    proxies: Optional[Dict] = None, timeout: int = 30):
        """Make a professional request with all protections"""
        
        # Rate limiting
        self.rate_limit()
        
        # Setup headers
        if headers is None:
            headers = {}
            
        headers['User-Agent'] = self.get_random_user_agent()
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
        # Setup proxies
        if proxies is None:
            proxies = self.get_next_proxy()
            
        # Make request with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=timeout
                )
                response.raise_for_status()
                
                # Check for blocking
                if self._is_blocked(response):
                    raise Exception("Access denied - likely blocked")
                    
                self.request_count += 1
                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                    
                # Exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 2)
                print(f"   ⚠️ Request failed, retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                
                # Rotate proxy on failure
                proxies = self.get_next_proxy()
                
    def _is_blocked(self, response):
        """Check if response indicates blocking"""
        blocked_indicators = [
            'access denied', 'blocked', 'captcha', 'cloudflare',
            'rate limit', 'too many requests', 'forbidden'
        ]
        
        text = response.text.lower()
        return any(indicator in text for indicator in blocked_indicators)

def create_service_account_config():
    """Create service account configuration file"""
    
    config = {
        "proxy_service": {
            "recommended": "smartproxy",
            "api_key": "YOUR_API_KEY_HERE",
            "endpoint": "YOUR_PROXY_ENDPOINT_HERE"
        },
        "rate_limiting": {
            "min_delay": 1.0,
            "max_delay": 3.0,
            "requests_per_minute": 20
        },
        "user_agents": {
            "rotation_enabled": True,
            "custom_list": []
        },
        "retry_config": {
            "max_retries": 3,
            "exponential_backoff": True
        },
        "data_sources": {
            "sec_edgar": {
                "enabled": True,
                "rate_limit": 0.1  # 100ms between requests
            },
            "finviz": {
                "enabled": True,
                "rate_limit": 2.0  # 2s between requests
            },
            "macrotrends": {
                "enabled": True,
                "rate_limit": 3.0  # 3s between requests
            },
            "tikr": {
                "enabled": True,
                "rate_limit": 4.0  # 4s between requests
            }
        }
    }
    
    with open('service_account_config.json', 'w') as f:
        json.dump(config, f, indent=2)
        
    print("✅ Created service_account_config.json")
    return config

def setup_environment():
    """Setup environment for professional scraping"""
    
    print("\n🔧 SETUP INSTRUCTIONS:")
    print("=" * 40)
    
    print("\n1️⃣ CHOOSE A PROXY SERVICE:")
    print("   - For professional use: SmartProxy ($75/month)")
    print("   - For enterprise: Bright Data ($500/month)")
    print("   - For quick setup: ProxyCrawl ($29/month)")
    
    print("\n2️⃣ GET API CREDENTIALS:")
    print("   - Sign up for your chosen service")
    print("   - Get API key and endpoint URL")
    print("   - Update service_account_config.json")
    
    print("\n3️⃣ INSTALL DEPENDENCIES:")
    print("   pip install requests beautifulsoup4 fake-useragent")
    
    print("\n4️⃣ TEST YOUR SETUP:")
    print("   python test_service_account.py")
    
    print("\n5️⃣ INTEGRATE WITH YOUR SCRAPERS:")
    print("   - Update your scraper files to use ProfessionalScraper")
    print("   - Replace direct requests with service account requests")
    
    print("\n💰 COST ESTIMATE:")
    print("   - Proxy service: $29-500/month")
    print("   - Expected success rate: 95-99%")
    print("   - Scalability: 1000+ requests/day")

if __name__ == "__main__":
    # Setup service account
    manager = ServiceAccountManager()
    proxy_services = manager.setup_proxy_service()
    
    # Create configuration
    config = create_service_account_config()
    
    # Setup instructions
    setup_environment()
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Choose a proxy service and sign up")
    print("2. Update service_account_config.json with your credentials")
    print("3. Test the setup with a few companies")
    print("4. Integrate with your existing scrapers")
    print("5. Monitor performance and adjust as needed") 