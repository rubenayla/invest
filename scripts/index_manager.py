#!/usr/bin/env python3
"""
Dynamic Index Manager
Fetches real market indices, caches company metadata, and tracks discovery dates.
"""

import json
import logging
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class IndexManager:
    """Manages dynamic index fetching with local caching and incremental updates."""
    
    def __init__(self, data_dir: str = 'data/indices'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.companies_file = self.data_dir / 'companies_registry.json'
        self.indices_file = self.data_dir / 'indices_cache.json'
        
        self.companies = self._load_companies_registry()
        self.indices_cache = self._load_indices_cache()
    
    def _load_companies_registry(self) -> Dict:
        """Load company metadata registry with discovery dates."""
        if self.companies_file.exists():
            try:
                with open(self.companies_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load companies registry: {e}")
        
        return {
            'companies': {},  # ticker -> {name, sector, discovered_date, indices, last_updated}
            'last_updated': None,
            'total_companies': 0
        }
    
    def _load_indices_cache(self) -> Dict:
        """Load cached index constituent lists."""
        if self.indices_file.exists():
            try:
                with open(self.indices_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load indices cache: {e}")
        
        return {
            'indices': {},  # index_name -> {tickers: [], last_updated: date}
            'refresh_intervals': {
                'sp500': 7,      # days - S&P changes rarely
                'ftse100': 30,   # monthly updates
                'dax': 30,       # quarterly reviews
                'nikkei225': 90, # less frequent changes
                'asx200': 90
            }
        }
    
    def _save_companies_registry(self):
        """Save companies registry atomically."""
        self.companies['last_updated'] = datetime.now().isoformat()
        self.companies['total_companies'] = len(self.companies['companies'])
        
        temp_file = self.companies_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.companies, f, indent=2)
            temp_file.rename(self.companies_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _save_indices_cache(self):
        """Save indices cache atomically."""
        temp_file = self.indices_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.indices_cache, f, indent=2)
            temp_file.rename(self.indices_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _needs_refresh(self, index_name: str) -> bool:
        """Check if index needs refreshing based on last update date."""
        if index_name not in self.indices_cache['indices']:
            return True
        
        last_updated = self.indices_cache['indices'][index_name].get('last_updated')
        if not last_updated:
            return True
        
        refresh_days = self.indices_cache['refresh_intervals'].get(index_name, 30)
        last_date = datetime.fromisoformat(last_updated)
        return (datetime.now() - last_date).days > refresh_days
    
    def _discover_company_info(self, ticker: str) -> Optional[Dict]:
        """Fetch basic company information and add to registry."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            company_data = {
                'name': info.get('longName') or info.get('shortName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'country': info.get('country', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'discovered_date': datetime.now().isoformat(),
                'indices': [],  # Will be populated when ticker is found in indices
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Discovered company: {ticker} - {company_data['name']}")
            return company_data
            
        except Exception as e:
            logger.warning(f"Could not fetch info for {ticker}: {e}")
            return None
    
    def _fetch_sp500_tickers(self) -> List[str]:
        """Fetch current S&P 500 constituents from Wikipedia."""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table', {'class': 'wikitable'})
            tickers = []
            
            for row in table.find_all('tr')[1:]:  # Skip header
                cells = row.find_all('td')
                if len(cells) > 0:
                    ticker = cells[0].text.strip()
                    tickers.append(ticker)
            
            logger.info(f"Fetched {len(tickers)} S&P 500 tickers from Wikipedia")
            return tickers
            
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500 from Wikipedia: {e}")
            return []
    
    def _fetch_ftse100_tickers(self) -> List[str]:
        """Fetch FTSE 100 constituents."""
        # For now, return a reasonable subset - could be enhanced with real API
        ftse100_core = [
            'SHEL', 'AZN', 'UL', 'BP.L', 'HSBA.L', 'VOD.L', 'GSK.L', 'RIO.L', 'BHP.L', 'BATS.L',
            'DGE.L', 'LLOY.L', 'NWG.L', 'BARC.L', 'PRU.L', 'REL.L', 'BT-A.L', 'AAL.L', 'AV.L', 'CRH.L'
        ]
        logger.info(f"Using FTSE 100 core list: {len(ftse100_core)} tickers")
        return ftse100_core
    
    def get_index_tickers(self, index_name: str, force_refresh: bool = False) -> List[str]:
        """Get tickers for an index, fetching if needed or using cache."""
        
        if force_refresh or self._needs_refresh(index_name):
            logger.info(f"Refreshing {index_name} index...")
            
            # Fetch based on index type
            if index_name == 'sp500':
                new_tickers = self._fetch_sp500_tickers()
            elif index_name == 'ftse100':
                new_tickers = self._fetch_ftse100_tickers()
            else:
                logger.warning(f"No fetcher implemented for {index_name}")
                new_tickers = []
            
            if new_tickers:
                # Update cache
                self.indices_cache['indices'][index_name] = {
                    'tickers': new_tickers,
                    'last_updated': datetime.now().isoformat(),
                    'count': len(new_tickers)
                }
                self._save_indices_cache()
                
                # Discover new companies
                self._update_company_registry(new_tickers, index_name)
                
                return new_tickers
        
        # Return cached version
        cached_data = self.indices_cache['indices'].get(index_name, {})
        return cached_data.get('tickers', [])
    
    def _update_company_registry(self, tickers: List[str], index_name: str):
        """Update company registry with new tickers from an index."""
        new_companies = 0
        
        for ticker in tickers:
            if ticker not in self.companies['companies']:
                # Discover new company
                company_info = self._discover_company_info(ticker)
                if company_info:
                    self.companies['companies'][ticker] = company_info
                    new_companies += 1
            
            # Add index to company's index list
            if ticker in self.companies['companies']:
                indices_list = self.companies['companies'][ticker].get('indices', [])
                if index_name not in indices_list:
                    indices_list.append(index_name)
                    self.companies['companies'][ticker]['indices'] = indices_list
        
        if new_companies > 0:
            logger.info(f"Discovered {new_companies} new companies from {index_name}")
            self._save_companies_registry()
    
    def get_all_tickers(self, max_age_days: int = 30) -> List[str]:
        """Get all known tickers, refreshing stale indices as needed."""
        all_tickers = set()
        
        # Define available indices
        available_indices = ['sp500', 'ftse100']
        
        for index_name in available_indices:
            tickers = self.get_index_tickers(index_name)
            all_tickers.update(tickers)
        
        return list(all_tickers)
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get cached company information."""
        return self.companies['companies'].get(ticker)
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        return {
            'total_companies': len(self.companies['companies']),
            'indices_cached': len(self.indices_cache['indices']),
            'last_registry_update': self.companies.get('last_updated'),
            'companies_by_index': {
                index: len([c for c in self.companies['companies'].values() 
                          if index in c.get('indices', [])])
                for index in self.indices_cache['indices'].keys()
            }
        }


if __name__ == '__main__':
    """Test the index manager."""
    logging.basicConfig(level=logging.INFO)
    
    manager = IndexManager()
    
    print("=== Index Manager Stats ===")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== Fetching S&P 500 ===")
    sp500_tickers = manager.get_index_tickers('sp500')
    print(f"S&P 500: {len(sp500_tickers)} tickers")
    
    print("\n=== All Tickers ===")
    all_tickers = manager.get_all_tickers()
    print(f"Total unique tickers: {len(all_tickers)}")
    
    if all_tickers:
        sample_ticker = all_tickers[0]
        company_info = manager.get_company_info(sample_ticker)
        print(f"\nSample company ({sample_ticker}):")
        print(json.dumps(company_info, indent=2))