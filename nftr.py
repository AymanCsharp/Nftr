#!/usr/bin/env python3

import os
import sys
import subprocess

def show_menu():
    print("""
███╗   ██╗███████╗████████╗██████╗ 
████╗  ██║██╔════╝╚══██╔══╝██╔══██╗
██╔██╗ ██║█████╗     ██║   ██████╔╝
██║╚██╗██║██╔══╝     ██║   ██╔══██╗
██║ ╚████║██║        ██║   ██║  ██║
╚═╝  ╚══╝╚═╝        ╚═╝   ╚═╝  ╚═╝

    NFTR WEB CRAWLER 
    Choose your crawler version:
    
    1. Basic Crawler
    2. Advanced Crawler
    3. Install Dependencies
    4. Exit
    
    Enter your choice (1-4): """)

def install_dependencies():
    print("Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("Error installing dependencies. Please install manually:")
        print("pip install -r requirements.txt")

def run_basic_crawler():
    if not os.path.exists("netr_crawler.py"):
        print("Basic crawler not found!")
        return
    
    print("\n=== NETR BASIC CRAWLER ===")
    print("Usage examples:")
    print("python netr_crawler.py https://example.com")
    print("python netr_crawler.py https://example.com -t 100 -d 0.01")
    print("python netr_crawler.py https://example.com -m 5000 -e csv")
    
    url = input("\nEnter URL to crawl: ").strip()
    if not url:
        print("No URL provided!")
        return
    
    threads = input("Number of threads (default 50): ").strip()
    delay = input("Delay between requests in seconds (default 0.1): ").strip()
    max_pages = input("Maximum pages to crawl (default 1000): ").strip()
    export_format = input("Export format (json/csv/sqlite, default json): ").strip()
    
    cmd = ["python", "netr_crawler.py", url]
    
    if threads:
        cmd.extend(["-t", threads])
    if delay:
        cmd.extend(["-d", delay])
    if max_pages:
        cmd.extend(["-m", max_pages])
    if export_format:
        cmd.extend(["-e", export_format])
    
    print(f"\nRunning command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user")

def run_advanced_crawler():
    if not os.path.exists("netr_advanced.py"):
        print("Advanced crawler not found!")
        return
    
    print("\n=== NETR ADVANCED CRAWLER ===")
    print("Usage examples:")
    print("python netr_advanced.py https://example.com")
    print("python netr_advanced.py https://example.com -t 200 -d 0.01")
    print("python netr_advanced.py https://example.com -p http://proxy:port")
    
    url = input("\nEnter URL to crawl: ").strip()
    if not url:
        print("No URL provided!")
        return
    
    threads = input("Number of threads (default 100): ").strip()
    delay = input("Delay between requests in seconds (default 0.05): ").strip()
    max_pages = input("Maximum pages to crawl (default 10000): ").strip()
    export_format = input("Export format (json/csv/sqlite, default json): ").strip()
    proxy = input("Proxy server (optional, format: http://host:port): ").strip()
    custom_headers = input("Custom headers (optional, format: key1:value1,key2:value2): ").strip()
    
    cmd = ["python", "netr_advanced.py", url]
    
    if threads:
        cmd.extend(["-t", threads])
    if delay:
        cmd.extend(["-d", delay])
    if max_pages:
        cmd.extend(["-m", max_pages])
    if export_format:
        cmd.extend(["-e", export_format])
    if proxy:
        cmd.extend(["-p", proxy])
    if custom_headers:
        cmd.extend(["--headers", custom_headers])
    
    print(f"\nRunning command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user")

def main():
    while True:
        show_menu()
        choice = input().strip()
        
        if choice == "1":
            run_basic_crawler()
        elif choice == "2":
            run_advanced_crawler()
        elif choice == "3":
            install_dependencies()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please enter 1-4")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
