from typing import Optional, List
import random
import time
import requests
from threading import Lock
from loguru import logger
import re
from bs4 import BeautifulSoup

class ProxyManager:
    def __init__(self, min_proxies: int = 5, timeout: int = 10):
        logger.info(f'Starting ProxyManager initialization with min_proxies={min_proxies}, timeout={timeout}')
        logger.info(f'Initialisiere ProxyManager mit min_proxies={min_proxies}, timeout={timeout}')
        self.min_proxies = min_proxies
        self.timeout = timeout
        self.proxies: List[str] = []
        self.current_index = 0
        self.lock = Lock()
        self.last_refresh = 0
        self.refresh_interval = 300  # 5 minutes
        self._current_proxy = None
        self._refresh_proxies()

    def _refresh_proxies(self):
        """Refresh the proxy list from multiple sources"""
        with self.lock:
            current_time = time.time()
            if current_time - self.last_refresh < self.refresh_interval and len(self.proxies) >= self.min_proxies:
                return

            logger.info("Refreshing proxy list from multiple sources...")
            new_proxies = []
            
            # Versuche verschiedene Proxy-Quellen
            proxy_sources = [
                self._get_spys_de_proxies,
                self._get_free_proxy_list,
                self._get_fallback_proxies
            ]
            
            for source_func in proxy_sources:
                if len(new_proxies) >= self.min_proxies:
                    break
                    
                try:
                    logger.info(f"Trying proxy source: {source_func.__name__}")
                    source_proxies = source_func()
                    
                    # Teste Proxies parallel (aber begrenzt)
                    for proxy in source_proxies[:10]:  # Maximal 10 pro Quelle testen
                        if len(new_proxies) >= self.min_proxies:
                            break
                        if self._test_proxy(proxy):
                            new_proxies.append(proxy)
                            logger.info(f"Working proxy found: {proxy}")
                            
                except Exception as e:
                    logger.warning(f"Proxy source {source_func.__name__} failed: {e}")
                    continue

            if new_proxies:
                self.proxies = new_proxies
                self.last_refresh = current_time
                self.current_index = 0
                logger.info(f"Successfully loaded {len(new_proxies)} working proxies")
            else:
                logger.warning("No working proxies found from any source")

    def _get_spys_de_proxies(self) -> List[str]:
        """Get German proxies from spys.one"""
        try:
            url = "https://spys.one/free-proxy-list/DE/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Einfache Regex-basierte Extraktion von IP:Port
            proxy_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})'
            matches = re.findall(proxy_pattern, response.text)
            
            proxies = [f"http://{ip}:{port}" for ip, port in matches]
            logger.info(f"Found {len(proxies)} German proxies from spys.one")
            return proxies[:20]  # Maximal 20 Proxies
            
        except Exception as e:
            logger.warning(f"Failed to get spys.one proxies: {e}")
            return []
    
    def _get_free_proxy_list(self) -> List[str]:
        """Get proxies from free-proxy-list.net"""
        try:
            url = "https://free-proxy-list.net/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Einfache Regex-Extraktion
            proxy_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d{2,5})'
            matches = re.findall(proxy_pattern, response.text)
            
            proxies = [f"http://{ip}:{port}" for ip, port in matches]
            logger.info(f"Found {len(proxies)} proxies from free-proxy-list.net")
            return proxies[:15]  # Maximal 15 Proxies
            
        except Exception as e:
            logger.warning(f"Failed to get free-proxy-list proxies: {e}")
            return []
    
    def _get_fallback_proxies(self) -> List[str]:
        """Fallback: Bekannte öffentliche Proxies (oft überlastet, aber als Backup)"""
        fallback_proxies = [
            "http://8.210.83.33:80",
            "http://47.74.152.29:8888",
            "http://43.134.68.153:3128",
            "http://103.149.162.194:80",
            "http://185.15.172.212:3128"
        ]
        logger.info(f"Using {len(fallback_proxies)} fallback proxies")
        return fallback_proxies

    def _test_proxy(self, proxy: str) -> bool:
        """Test if a proxy is working with faster timeout"""
        try:
            test_url = "https://httpbin.org/ip"  # Schnellerer Test-Endpoint
            proxies = {
                "http": proxy,
                "https": proxy
            }
            response = requests.get(test_url, proxies=proxies, timeout=5)  # Kürzerer Timeout
            return response.status_code == 200
        except Exception:
            return False

    @property
    def current_proxy(self) -> Optional[str]:
        """Gibt den aktuell verwendeten Proxy zurück"""
        return self._current_proxy

    def get_proxy(self) -> Optional[str]:
        """Get the next working proxy"""
        self._refresh_proxies()
        
        if not self.proxies:
            self._current_proxy = None
            return None

        with self.lock:
            self._current_proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            logger.info(f"Using proxy: {self._current_proxy}")
            return self._current_proxy

    def get_request_kwargs(self) -> dict:
        """Get request kwargs with proxy settings"""
        proxy = self.get_proxy()
        if not proxy:
            return {}
            
        return {
            "proxies": {
                "http": proxy,
                "https": proxy
            },
            "timeout": self.timeout
        }
