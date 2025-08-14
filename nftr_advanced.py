import requests
import threading
import queue
import time
import re
import urllib.parse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import json
import csv
import sqlite3
import hashlib
import os
import random
import ssl
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys
from datetime import datetime
import hashlib
import base64

class NetrAdvancedCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Netr-Crawler/3.0 (Ultimate Web Intelligence Tool)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.visited_urls = set()
        self.url_queue = queue.Queue()
        self.results = []
        self.robots_cache = {}
        self.max_threads = 100
        self.delay = 0.05
        self.max_depth = 10
        self.max_pages = 10000
        self.proxies = []
        self.custom_headers = {}
        self.extract_patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phones': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'urls': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            'social_media': r'(?:facebook\.com|twitter\.com|linkedin\.com|instagram\.com|youtube\.com|tiktok\.com|snapchat\.com)/[^\s<>"\']+',
            'bitcoin': r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',
            'ethereum': r'0x[a-fA-F0-9]{40}',
            'credit_cards': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'ip_addresses': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'mac_addresses': r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b',
            'file_paths': r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
            'api_keys': r'[a-zA-Z0-9]{32,}',
            'jwt_tokens': r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            'aws_keys': r'AKIA[0-9A-Z]{16}',
            'google_keys': r'AIza[0-9A-Za-z-_]{35}',
            'github_tokens': r'ghp_[a-zA-Z0-9]{36}'
        }
        self.security_headers = [
            'X-Frame-Options', 'X-Content-Type-Options', 'X-XSS-Protection',
            'Strict-Transport-Security', 'Content-Security-Policy', 'Referrer-Policy'
        ]
        
    def show_banner(self):
        banner = """
███████╗███╗   ██╗███████╗████████╗██████╗     █████  ██████╗ ██╗     ██╗   ██╗███████╗██████╗ 
██╔════╝████╗  ██║██╔════╝╚══██╔══╝██╔══██╗    ██╔══██╗██╔══██╗██║     ██║   ██║██╔════╝██╔══██╗
█████╗  ██╔██╗ ██║█████╗     ██║   ██████╔╝    ███████║██║  ██║██║     ██║   ██║█████╗  ██████╔╝
██╔══╝  ██║╚██╗██║██╔══╝     ██║   ██╔══██╗    ██╔══██║██║  ██║██║     ██║   ██║██╔══╝  ██╔══██╗
███████╗██║ ╚████║██║        ██║   ██║  ██║    ██║  ██║██████╔╝███████╗╚██████╔╝███████╗██║  ██║
╚══════╝╚═╝  ╚══╝╚═╝        ╚═╝   ╚═╝  ╚═╝    ╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                                    
                    ULTIMATE WEB CRAWLER & INTELLIGENCE GATHERING TOOL
                    Version 3.0 - The Most Advanced Crawler Ever Created
                    """
        print(banner)
        
    def add_proxy(self, proxy):
        self.proxies.append(proxy)
        
    def set_custom_headers(self, headers):
        self.custom_headers.update(headers)
        self.session.headers.update(headers)
        
    def get_random_proxy(self):
        if self.proxies:
            return random.choice(self.proxies)
        return None
        
    def check_robots_txt(self, base_url):
        if base_url in self.robots_cache:
            return self.robots_cache[base_url]
            
        try:
            robots_url = urllib.parse.urljoin(base_url, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            self.robots_cache[base_url] = rp
            return rp
        except:
            return None
            
    def can_fetch(self, url, user_agent='*'):
        base_url = urllib.parse.urlparse(url).netloc
        rp = self.check_robots_txt(f"https://{base_url}")
        if rp:
            return rp.can_fetch(user_agent, url)
        return True
        
    def analyze_security_headers(self, response):
        security_info = {}
        for header in self.security_headers:
            if header in response.headers:
                security_info[header] = response.headers[header]
        return security_info
        
    def analyze_ssl_certificate(self, url):
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme == 'https':
                context = ssl.create_default_context()
                with socket.create_connection((parsed.netloc, 443)) as sock:
                    with context.wrap_socket(sock, server_hostname=parsed.netloc) as ssock:
                        cert = ssock.getpeercert()
                        return {
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'subject': dict(x[0] for x in cert['subject']),
                            'version': cert['version'],
                            'serial_number': cert['serialNumber'],
                            'not_before': cert['notBefore'],
                            'not_after': cert['notAfter']
                        }
        except:
            return None
            
    def extract_data(self, html, url, response):
        soup = BeautifulSoup(html, 'html.parser')
        extracted = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': soup.title.string if soup.title else '',
            'meta_description': '',
            'meta_keywords': '',
            'meta_viewport': '',
            'meta_charset': '',
            'links': [],
            'images': [],
            'forms': [],
            'tables': [],
            'text_content': '',
            'structured_data': [],
            'security_headers': self.analyze_security_headers(response),
            'ssl_certificate': self.analyze_ssl_certificate(url),
            'response_headers': dict(response.headers),
            'status_code': response.status_code,
            'content_length': len(response.content),
            'content_type': response.headers.get('content-type', ''),
            'server': response.headers.get('server', ''),
            'x_powered_by': response.headers.get('x-powered-by', ''),
            'technologies': [],
            'vulnerabilities': [],
            'secrets': {}
        }
        
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                extracted['meta_description'] = meta.get('content', '')
            elif meta.get('name') == 'keywords':
                extracted['meta_keywords'] = meta.get('content', '')
            elif meta.get('name') == 'viewport':
                extracted['meta_viewport'] = meta.get('content', '')
            elif meta.get('charset'):
                extracted['meta_charset'] = meta.get('charset', '')
                
        for link in soup.find_all('a', href=True):
            extracted['links'].append({
                'text': link.get_text(strip=True),
                'href': link['href'],
                'title': link.get('title', ''),
                'rel': link.get('rel', []),
                'target': link.get('target', '')
            })
            
        for img in soup.find_all('img'):
            extracted['images'].append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
            
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', ''),
                'enctype': form.get('enctype', ''),
                'inputs': []
            }
            for input_tag in form.find_all('input'):
                form_data['inputs'].append({
                    'type': input_tag.get('type', ''),
                    'name': input_tag.get('name', ''),
                    'value': input_tag.get('value', ''),
                    'placeholder': input_tag.get('placeholder', ''),
                    'required': input_tag.get('required', False)
                })
            extracted['forms'].append(form_data)
            
        for table in soup.find_all('table'):
            table_data = []
            for row in table.find_all('tr'):
                row_data = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if row_data:
                    table_data.append(row_data)
            extracted['tables'].append(table_data)
            
        text_content = soup.get_text()
        extracted['text_content'] = ' '.join(text_content.split())
        
        for pattern_name, pattern in self.extract_patterns.items():
            matches = re.findall(pattern, text_content)
            if matches:
                extracted['secrets'][pattern_name] = list(set(matches))
                
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                extracted['structured_data'].append(data)
            except:
                pass
                
        for script in soup.find_all('script'):
            src = script.get('src', '')
            if src:
                if 'jquery' in src.lower():
                    extracted['technologies'].append('jQuery')
                if 'react' in src.lower():
                    extracted['technologies'].append('React')
                if 'angular' in src.lower():
                    extracted['technologies'].append('Angular')
                if 'vue' in src.lower():
                    extracted['technologies'].append('Vue.js')
                    
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if 'bootstrap' in href.lower():
                extracted['technologies'].append('Bootstrap')
            if 'tailwind' in href.lower():
                extracted['technologies'].append('Tailwind CSS')
                
        return extracted
        
    def crawl_page(self, url, depth=0):
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return None
            
        if url in self.visited_urls:
            return None
            
        if not self.can_fetch(url):
            return None
            
        self.visited_urls.add(url)
        
        try:
            proxy = self.get_random_proxy()
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            
            response = self.session.get(url, timeout=15, proxies=proxies)
            if response.status_code == 200:
                extracted_data = self.extract_data(response.text, url, response)
                self.results.append(extracted_data)
                
                if depth < self.max_depth:
                    for link in extracted_data['links']:
                        full_url = urllib.parse.urljoin(url, link['href'])
                        if full_url not in self.visited_urls:
                            self.url_queue.put((full_url, depth + 1))
                            
                return extracted_data
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            
        return None
        
    def start_crawling(self, start_url, max_threads=None, delay=None):
        if max_threads:
            self.max_threads = max_threads
        if delay:
            self.delay = delay
            
        self.url_queue.put((start_url, 0))
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            
            while not self.url_queue.empty() and len(self.visited_urls) < self.max_pages:
                try:
                    url, depth = self.url_queue.get_nowait()
                    future = executor.submit(self.crawl_page, url, depth)
                    futures.append(future)
                    time.sleep(self.delay)
                except queue.Empty:
                    break
                    
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception as e:
                    print(f"Thread error: {str(e)}")
                    
    def export_results(self, format_type='json', filename='netr_advanced_results'):
        if format_type == 'json':
            with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        elif format_type == 'csv':
            with open(f"{filename}.csv", 'w', newline='', encoding='utf-8') as f:
                if self.results:
                    writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                    writer.writeheader()
                    for result in self.results:
                        writer.writerow(result)
        elif format_type == 'sqlite':
            conn = sqlite3.connect(f"{filename}.db")
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS advanced_crawled_data
                (url TEXT, title TEXT, meta_description TEXT, links_count INTEGER, 
                 images_count INTEGER, forms_count INTEGER, text_length INTEGER,
                 technologies TEXT, security_score INTEGER, secrets_count INTEGER)
            ''')
            
            for result in self.results:
                technologies = ', '.join(result.get('technologies', []))
                secrets_count = len(result.get('secrets', {}))
                security_score = len(result.get('security_headers', {}))
                
                cursor.execute('''
                    INSERT INTO advanced_crawled_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['url'],
                    result['title'],
                    result['meta_description'],
                    len(result['links']),
                    len(result['images']),
                    len(result['forms']),
                    len(result['text_content']),
                    technologies,
                    security_score,
                    secrets_count
                ))
            conn.commit()
            conn.close()
            
    def show_statistics(self):
        if not self.results:
            print("No data crawled yet.")
            return
            
        total_pages = len(self.results)
        total_links = sum(len(r['links']) for r in self.results)
        total_images = sum(len(r['images']) for r in self.results)
        total_forms = sum(len(r['forms']) for r in self.results)
        
        print(f"\n=== NETR ADVANCED CRAWLING STATISTICS ===")
        print(f"Total Pages Crawled: {total_pages}")
        print(f"Total Links Found: {total_links}")
        print(f"Total Images Found: {total_images}")
        print(f"Total Forms Found: {total_forms}")
        print(f"Average Links per Page: {total_links/total_pages:.2f}")
        print(f"Average Images per Page: {total_images/total_pages:.2f}")
        print(f"Average Forms per Page: {total_forms/total_pages:.2f}")
        
        if self.results:
            all_secrets = {}
            all_technologies = set()
            security_scores = []
            
            for result in self.results:
                if 'secrets' in result:
                    for secret_type, secrets in result['secrets'].items():
                        if secret_type not in all_secrets:
                            all_secrets[secret_type] = set()
                        all_secrets[secret_type].update(secrets)
                        
                if 'technologies' in result:
                    all_technologies.update(result['technologies'])
                    
                if 'security_headers' in result:
                    security_scores.append(len(result['security_headers']))
                    
            print(f"\n=== SECURITY ANALYSIS ===")
            print(f"Average Security Headers: {sum(security_scores)/len(security_scores):.2f}")
            print(f"Technologies Detected: {', '.join(all_technologies)}")
            
            print(f"\n=== SECRETS DISCOVERED ===")
            for secret_type, secrets in all_secrets.items():
                print(f"{secret_type.title()}: {len(secrets)} unique values")

def main():
    parser = argparse.ArgumentParser(description='Netr Advanced - Ultimate Web Crawler')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('-t', '--threads', type=int, default=100, help='Number of threads (default: 100)')
    parser.add_argument('-d', '--delay', type=float, default=0.05, help='Delay between requests (default: 0.05s)')
    parser.add_argument('-m', '--max-pages', type=int, default=10000, help='Maximum pages to crawl (default: 10000)')
    parser.add_argument('-e', '--export', choices=['json', 'csv', 'sqlite'], default='json', help='Export format')
    parser.add_argument('-o', '--output', default='netr_advanced_results', help='Output filename')
    parser.add_argument('-p', '--proxy', help='Proxy server (format: http://user:pass@host:port)')
    parser.add_argument('--headers', help='Custom headers (format: key1:value1,key2:value2)')
    
    args = parser.parse_args()
    
    crawler = NetrAdvancedCrawler()
    crawler.show_banner()
    
    if args.proxy:
        crawler.add_proxy(args.proxy)
        
    if args.headers:
        headers = {}
        for header in args.headers.split(','):
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
        crawler.set_custom_headers(headers)
    
    print(f"\nStarting advanced crawl of: {args.url}")
    print(f"Threads: {args.threads}")
    print(f"Delay: {args.delay}s")
    print(f"Max Pages: {args.max_pages}")
    print(f"Export Format: {args.export}")
    if args.proxy:
        print(f"Using Proxy: {args.proxy}")
    
    start_time = time.time()
    crawler.max_pages = args.max_pages
    crawler.start_crawling(args.url, args.threads, args.delay)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nAdvanced crawling completed in {duration:.2f} seconds")
    crawler.show_statistics()
    
    print(f"\nExporting results to {args.output}.{args.export}")
    crawler.export_results(args.export, args.output)
    print("Export completed!")

if __name__ == "__main__":
    main()
