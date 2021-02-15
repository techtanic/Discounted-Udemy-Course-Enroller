import requests
import urllib3
from bs4 import BeautifulSoup
import json
from .constants import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def udemy_freebies(page):
    links_ls = []
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }

    r = requests.get("https://www.udemyfreebies.com/free-udemy-courses/" +
                     str(page), headers=head, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    all = soup.find_all('div', 'theme-block')
    for index, items in enumerate(all):
        # Removed the extra get request by changing the url
        title = items.img['title']
        url2 = items.a['href']
        url3 = url2.split("/")
        url3[-2] = "out"
        # r2 = requests.get(url2, headers=head, verify=False)
        # soup1 = BeautifulSoup(r2.content, 'html.parser')
        # url3 = soup1.find('a', class_ = 'button-icon')['href']
        link = requests.get('/'.join(url3), verify=False).url
        links_ls.append(title + '|:|' + link)
    return links_ls


def discudemy(page):
    links_ls = []
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }

    r = requests.get(DISCUD + str(page), headers=head, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    all = soup.find_all('section', 'card')
    for index, items in enumerate(all):
        try:
            title = items.a.text
            url2 = items.a['href']
        except:
            title = ''
            url2 = ''
        if url2 != '':
            # r2 = requests.get(url2, headers=head, verify=False)
            # soup1 = BeautifulSoup(r2.content, 'html.parser')
            # next = soup1.find('div', 'ui center aligned basic segment')
            # url3 = next.a['href']
            # r3 = requests.get(url3, headers=head, verify=False)
            # Removed the extra get request by changing the url
            url3 = url2.split('/')
            url3[-2] = "go"
            r3 = requests.get('/'.join(url3), headers=head, verify=False)
            soup3 = BeautifulSoup(r3.content, 'html.parser')
            links_ls.append(
                title + '|:|' + soup3.find('div', 'ui segment').a['href'])
    return links_ls


def course_mania(page):
    links_ls = []
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Referer': 'https://coursemania.xyz/',
        'Origin': 'https://coursemania.xyz',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }

    r = requests.get(COURSEMANIA, headers=head, verify=False)
    js = r.json()
    for items in js:
        title = items['courseName']
        link = items['url']
        links_ls.append(title + '|:|' + link)
    return links_ls
