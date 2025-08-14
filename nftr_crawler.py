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
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys

class NetrCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Netr-Crawler/2.0 (Advanced Web Intelligence Tool)'
        })
        self.visited_urls = set()
        self.url_queue = queue.Queue()
        self.results = []
        self.robots_cache = {}
        self.max_threads = 50
        self.delay = 0.1
        self.max_depth = 5
        self.max_pages = 1000
        self.extract_patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phones': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'urls': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            'social_media': r'(?:facebook\.com|twitter\.com|linkedin\.com|instagram\.com|youtube\.com)/[^\s<>"\']+',
            'bitcoin': r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',
            'ethereum': r'0x[a-fA-F0-9]{40}'
        }
        
    def show_banner(self):
        banner = """
███╗   ██╗███████╗████████╗██████╗ 
████╗  ██║██╔════╝╚══██╔══╝██╔══██╗
██╔██╗ ██║█████╗     ██║   ██████╔╝
██║╚██╗██║██╔══╝     ██║   ██╔══██╗
██║ ╚████║██║        ██║   ██║  ██║
╚═╝  ╚══╝╚═╝        ╚═╝   ╚═╝  ╚═╝
                                    
    NFTR WEB CRAWLER
    Version 2.0 - The Most Powerful Crawler Ever Created
    """
        print(banner)
        
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
        
    def extract_data(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        extracted = {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'meta_description': '',
            'meta_keywords': '',
            'links': [],
            'images': [],
            'forms': [],
            'tables': [],
            'text_content': '',
            'structured_data': []
        }
        
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                extracted['meta_description'] = meta.get('content', '')
            elif meta.get('name') == 'keywords':
                extracted['meta_keywords'] = meta.get('content', '')
                
        for link in soup.find_all('a', href=True):
            extracted['links'].append({
                'text': link.get_text(strip=True),
                'href': link['href'],
                'title': link.get('title', '')
            })
            
        for img in soup.find_all('img'):
            extracted['images'].append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
            
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', ''),
                'inputs': []
            }
            for input_tag in form.find_all('input'):
                form_data['inputs'].append({
                    'type': input_tag.get('type', ''),
                    'name': input_tag.get('name', ''),
                    'value': input_tag.get('value', '')
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
                extracted[pattern_name] = list(set(matches))
                
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                extracted['structured_data'].append(data)
            except:
                pass
                
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
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                extracted_data = self.extract_data(response.text, url)
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
                    
    def export_results(self, format_type='json', filename='netr_results'):
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
                CREATE TABLE IF NOT EXISTS crawled_data
                (url TEXT, title TEXT, meta_description TEXT, links_count INTEGER, 
                 images_count INTEGER, forms_count INTEGER, text_length INTEGER)
            ''')
            
            for result in self.results:
                cursor.execute('''
                    INSERT INTO crawled_data VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['url'],
                    result['title'],
                    result['meta_description'],
                    len(result['links']),
                    len(result['images']),
                    len(result['forms']),
                    len(result['text_content'])
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
        
        print(f"\n=== NETR CRAWLING STATISTICS ===")
        print(f"Total Pages Crawled: {total_pages}")
        print(f"Total Links Found: {total_links}")
        print(f"Total Images Found: {total_images}")
        print(f"Total Forms Found: {total_forms}")
        print(f"Average Links per Page: {total_links/total_pages:.2f}")
        print(f"Average Images per Page: {total_images/total_pages:.2f}")
        print(f"Average Forms per Page: {total_forms/total_pages:.2f}")
        
        if self.results:
            emails = set()
            phones = set()
            social_media = set()
            
            for result in self.results:
                if 'emails' in result:
                    emails.update(result['emails'])
                if 'phones' in result:
                    phones.update(result['phones'])
                if 'social_media' in result:
                    social_media.update(result['social_media'])
                    
            print(f"Unique Emails Found: {len(emails)}")
            print(f"Unique Phone Numbers: {len(phones)}")
            print(f"Social Media Links: {len(social_media)}")

def main():
    parser = argparse.ArgumentParser(description='Netr - Advanced Web Crawler')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('-t', '--threads', type=int, default=50, help='Number of threads (default: 50)')
    parser.add_argument('-d', '--delay', type=float, default=0.1, help='Delay between requests (default: 0.1s)')
    parser.add_argument('-m', '--max-pages', type=int, default=1000, help='Maximum pages to crawl (default: 1000)')
    parser.add_argument('-e', '--export', choices=['json', 'csv', 'sqlite'], default='json', help='Export format')
    parser.add_argument('-o', '--output', default='netr_results', help='Output filename')
    
    args = parser.parse_args()
    
    crawler = NetrCrawler()
    crawler.show_banner()
    
    print(f"\nStarting crawl of: {args.url}")
    print(f"Threads: {args.threads}")
    print(f"Delay: {args.delay}s")
    print(f"Max Pages: {args.max_pages}")
    print(f"Export Format: {args.export}")
    
    start_time = time.time()
    crawler.max_pages = args.max_pages
    crawler.start_crawling(args.url, args.threads, args.delay)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nCrawling completed in {duration:.2f} seconds")
    crawler.show_statistics()
    
    print(f"\nExporting results to {args.output}.{args.export}")
    crawler.export_results(args.export, args.output)
    print("Export completed!")

if __name__ == "__main__":
    main()
