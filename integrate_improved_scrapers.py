#!/usr/bin/env python3
"""
Integrate all improved scrapers into the main app
"""

def integrate_improved_scrapers():
    """Integrate all improved scrapers into the main app.py file"""
    
    # Read the current app.py file
    with open('financial-models-app/backend/app.py', 'r') as f:
        content = f.read()
    
    # Replace the old scraping functions with improved ones
    
    # 1. Replace SEC EDGAR scraping
    old_sec_function = """def scrape_edgar_sec_data(ticker):
    \"\"\"Scrape SEC EDGAR data for a given ticker\"\"\"
    try:
        # Use SEC's JSON API for better reliability
        cik = ticker.zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        facts = data.get('facts', {})
        
        # Extract key metrics
        revenue = None
        if 'us-gaap:Revenues' in facts:
            units = facts['us-gaap:Revenues'].get('units', {})
            for unit_type, values in units.items():
                if unit_type in ['USD', 'usd']:
                    annual_values = [v for v in values if v.get('form') == '10-K']
                    if annual_values:
                        revenue = max(annual_values, key=lambda x: x.get('end', ''))
                        break
        
        return {
            'sec_revenue': revenue.get('val') if revenue else None,
            'data_quality': 'high' if revenue else 'low'
        }
        
    except Exception as e:
        print(f"   ⚠️ SEC EDGAR error: {e}")
        return None"""
    
    new_sec_function = """def scrape_edgar_sec_data(ticker):
    \"\"\"Improved SEC EDGAR data scraping with better error handling\"\"\"
    try:
        from improve_sec_scraping import improved_scrape_edgar_sec_data
        return improved_scrape_edgar_sec_data(ticker)
    except ImportError:
        # Fallback to original method if improved scraper not available
        try:
            cik = ticker.zfill(10)
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            facts = data.get('facts', {})
            
            revenue = None
            if 'us-gaap:Revenues' in facts:
                units = facts['us-gaap:Revenues'].get('units', {})
                for unit_type, values in units.items():
                    if unit_type in ['USD', 'usd']:
                        annual_values = [v for v in values if v.get('form') == '10-K']
                        if annual_values:
                            revenue = max(annual_values, key=lambda x: x.get('end', ''))
                            break
            
            return {
                'sec_revenue': revenue.get('val') if revenue else None,
                'data_quality': 'high' if revenue else 'low'
            }
            
        except Exception as e:
            print(f"   ⚠️ SEC EDGAR error: {e}")
            return None"""
    
    content = content.replace(old_sec_function, new_sec_function)
    
    # 2. Replace Finviz scraping
    old_finviz_function = """def scrape_finviz_data(ticker):
    \"\"\"Scrape Finviz data for a given ticker\"\"\"
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return parse_finviz_data(soup)
        
    except Exception as e:
        print(f"   ⚠️ Finviz error: {e}")
        return None"""
    
    new_finviz_function = """def scrape_finviz_data(ticker):
    \"\"\"Improved Finviz data scraping with better error handling\"\"\"
    try:
        from improve_finviz_scraping import improved_scrape_finviz_data
        return improved_scrape_finviz_data(ticker)
    except ImportError:
        # Fallback to original method if improved scraper not available
        try:
            url = f"https://finviz.com/quote.ashx?t={ticker}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return parse_finviz_data(soup)
            
        except Exception as e:
            print(f"   ⚠️ Finviz error: {e}")
            return None"""
    
    content = content.replace(old_finviz_function, new_finviz_function)
    
    # 3. Replace Macrotrends scraping
    old_macrotrends_function = """def scrape_macrotrends_data(ticker):
    \"\"\"Scrape Macrotrends data for a given ticker\"\"\"
    try:
        url = f"https://www.macrotrends.net/stocks/charts/{ticker}/financial-statements"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return parse_macrotrends_data(soup)
        
    except Exception as e:
        print(f"   ⚠️ Macrotrends error: {e}")
        return None"""
    
    new_macrotrends_function = """def scrape_macrotrends_data(ticker):
    \"\"\"Improved Macrotrends data scraping with better error handling\"\"\"
    try:
        from improve_macrotrends_scraping import improved_scrape_macrotrends_data
        return improved_scrape_macrotrends_data(ticker)
    except ImportError:
        # Fallback to original method if improved scraper not available
        try:
            url = f"https://www.macrotrends.net/stocks/charts/{ticker}/financial-statements"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return parse_macrotrends_data(soup)
            
        except Exception as e:
            print(f"   ⚠️ Macrotrends error: {e}")
            return None"""
    
    content = content.replace(old_macrotrends_function, new_macrotrends_function)
    
    # 4. Replace Tikr scraping
    old_tikr_function = """def scrape_tikr_data(ticker):
    \"\"\"Scrape Tikr data for a given ticker\"\"\"
    try:
        url = f"https://tikr.com/{ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return parse_tikr_html_data(soup)
        
    except Exception as e:
        print(f"   ⚠️ Tikr error: {e}")
        return None"""
    
    new_tikr_function = """def scrape_tikr_data(ticker):
    \"\"\"Improved Tikr data scraping with better error handling\"\"\"
    try:
        from improve_tikr_scraping import improved_scrape_tikr_data
        return improved_scrape_tikr_data(ticker)
    except ImportError:
        # Fallback to original method if improved scraper not available
        try:
            url = f"https://tikr.com/{ticker}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return parse_tikr_html_data(soup)
            
        except Exception as e:
            print(f"   ⚠️ Tikr error: {e}")
            return None"""
    
    content = content.replace(old_tikr_function, new_tikr_function)
    
    # Write the updated content back
    with open('financial-models-app/backend/app.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully integrated improved scrapers into app.py")
    print("📋 Improvements added:")
    print("   - Better rate limiting and retry logic")
    print("   - Anti-blocking measures")
    print("   - Multiple endpoint redundancy")
    print("   - Data quality validation")
    print("   - Fallback to original methods if improved scrapers unavailable")

if __name__ == "__main__":
    integrate_improved_scrapers() 