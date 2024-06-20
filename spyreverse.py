import validators
import socket
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import os
import platform
import colorama
import threading
from queue import Queue

colorama.init()
fg = [
    '\033[91;1m',  # red 0
    '\033[92;1m',  # green 1
    '\033[93;1m',  # yellow 2
    '\033[94;1m',  # blue 3
    '\033[95;1m',  # magenta 4
    '\033[96;1m',  # cyan 5
    '\033[97;1m'  # white 6
]


def clear():
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def banner():
    clear()
    print('''
  
        {0}   _____             _____                              
        {0}  / ____|           |  __ \                             
        {1} | (___  _ __  _   _| |__) |_____   _____ _ __ ___  ___ 
        {1}  \___ \| '_ \| | | |  _  // _ \ \ / / _ \ '__/ __|/ _ /
        {2}  ____) | |_) | |_| | | \ \  __/\ V /  __/ |  \__ \  __/
        {2} |_____/| .__/ \__, |_|  \_\___| \_/ \___|_|  |___/\___|
        {3}        | |     __/ |                                   
        {3}        |_|    |___/   channel : @spydev_channel                                   
       {2}\━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━/
       \t├╼ {3}BY : spydev{2}
       \t└╼ {3}Multi Website Grabber
    \033[0m'''.format(fg[1], fg[0], fg[5], fg[3]))


def get_website_ip(website):
    try:
        hostname = urlparse(website).hostname
        return website, socket.gethostbyname(hostname)
    except socket.gaierror:
        return website, None


def process_websites_thread(website_queue, output_file, total_websites):
    with open(output_file, "a") as f:
        while not website_queue.empty():
            i, website = website_queue.get()
            _, ip = get_website_ip(website)
            if ip:
                output = f"Converting {i}/{total_websites}: {fg[1]}Website {website} is {ip}\033[0m"
                f.write(ip + "\n")
            else:
                output = f"Converting {i}/{total_websites}: {fg[0]}Error: Couldn't resolve IP for \033[0m{website}"
            print(f"\r{' ' * 100}", end="", flush=True)  # Clear previous output
            print(f"\r{output}", end="", flush=True)
            website_queue.task_done()


def read_ips_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


def extract_domains_for_ip_thread(ip_queue, output_file):
    while not ip_queue.empty():
        ip, domain_count = ip_queue.get()
        base_url = "https://rapiddns.io/sameip/"
        page = 1
        extracted_count = 0
        last_page_number = 1

        while True:
            url = f"{base_url}{ip}?page={page}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            if domain_count == 0:
                pagination = soup.find('ul', class_='pagination')
                if pagination:
                    all_pages = pagination.find_all('a', class_='page-link')
                    last_page_link = all_pages[-2].get('href')
                    last_page_number = int(last_page_link.split('=')[-1])
                    domain_count = len(soup.find_all('tr')) * last_page_number

            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) > 1:
                    domain = cols[0].text.strip()
                    extracted_count += 1
                    with open(output_file, 'a') as file:
                        file.write(domain + '\n')
                    print(f"\r{' ' * 100}", end="", flush=True)  # Clear previous output
                    print(f"\rExtracting [{extracted_count}/{domain_count}] from {ip} : {domain}", end='', flush=True)

            if page >= last_page_number:
                break
            page += 1

        ip_queue.task_done()


def extract_domains_from_ips(file_path, output_file='extracted.txt', threads=5):
    ips = read_ips_from_file(file_path)
    ip_queue = Queue()

    for ip in ips:
        ip_queue.put((ip, 0))

    for _ in range(threads):
        thread = threading.Thread(target=extract_domains_for_ip_thread, args=(ip_queue, output_file))
        thread.start()

    ip_queue.join()


def main():
    banner()
    file_path = input("Enter your file path: ")
    IPs_count = 0
    website_count = 0
    ip_list = []
    website_list = []

    with open(file_path) as file:
        for line in file:
            entry = line.strip()
            if entry:
                if validators.url(entry):
                    website_count += 1
                    website_list.append(entry)
                elif validators.ipv4(entry) or validators.ipv6(entry):
                    IPs_count += 1
                    ip_list.append(entry)

    print(f"Number of websites: {website_count}")
    print(f"Number of IPs : {IPs_count}")

    if website_count > 0:
        print(f"Converting {website_count} URLs to IPs")

        website_queue = Queue()
        output_file = "output.txt"
        for i, website in enumerate(website_list, start=1):
            website_queue.put((i, website))

        for _ in range(10):  # 10 threads for processing websites
            thread = threading.Thread(target=process_websites_thread, args=(website_queue, output_file, website_count))
            thread.start()

        website_queue.join()

        with open(output_file) as f:
            unique_ips = len(set(f.readlines()))
        print(f"\nTotal IPs: {unique_ips}")

        print("Output written to output.txt")

    if IPs_count > 0 or website_count > 0:
        extract_domains_from_ips('output.txt' if website_count > 0 else file_path)


main()
