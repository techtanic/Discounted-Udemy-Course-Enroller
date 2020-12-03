import argparse
import random
import re
import sys
import time
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import browser_cookie3
import colorama
import requests
import urllib3
from bs4 import BeautifulSoup

from pack.banner import banner
from pack.colors import *
from pack.constants import CHECKOUT, site_range, total_sites
from pack.functions import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

func_list = [
    lambda page : discudemy(page),
    lambda page : udemy_freebies(page),
    lambda page : udemy_coupons_me(page),
    lambda page : real_disc(page),
    lambda page : tricksinfo(page),
    lambda page : freewebcart(page),
    lambda page : course_mania(page),
    lambda page : jojocoupons(page),
]


with open("config.json") as f:
    global currency
    currency = json.load(f)
    currency = currency["currency"]

def cookiejar(client_id, access_token):
    cookies = dict(client_id=client_id, access_token=access_token)
    return cookies

def getRealUrl(url):
    path = url.split(".com/")[1]
    return "https://www.udemy.com/" + path

def get_course_id(url, cookies):
    global purchased_text
    r2 = requests.get(url, verify=False, cookies=cookies)
    soup = BeautifulSoup(r2.content, 'html.parser')
    try:
        purchased_text = soup.find('div', class_ = 'purchase-text').text.replace("\n","")
    except:
        purchased_text = ''
    try:
        courseid = soup.find('body', attrs = {'id': 'udemy'})['data-clp-course-id']
    except:
        try:
            courseid = j[1]['sku'].replace('course:', '')
        except:
            soupx = soup.find('div', class_ = 'ud-component--course-landing-page-udlite--buy-button-cacheable')
            if soupx != None:
                likk = soupx.find('a')['href']
                courseid = int(re.search(r'\d+', likk).group(0))
            else:
                courseid = 'dsad'
    return courseid


def get_course_coupon(url):
    query = urlsplit(url).query
    params = parse_qs(query)
    try:
        params = {k: v[0] for k, v in params.items()}
        return params['couponCode']
    except:
        return ''

def free_checkout(CHECKOUT, access_token, csrftoken, coupon, courseID, cookies, head):
    payload = '{"shopping_cart":{"items":[{"buyableType":"course","buyableId":' + str(courseID) + ',"discountInfo":{"code":"' + coupon + '"},"purchasePrice":{"currency":"' + currency + '","currency_symbol":"","amount":0,"price_string":"Free"},"buyableContext":{"contentLocaleId":null}}]},"payment_info":{"payment_vendor":"Free","payment_method":"free-method"}}'

    r = requests.post(CHECKOUT, headers=head, data=payload, cookies=cookies, verify=False)
    return r.json()

def free_enroll(courseID, access_token, cookies, csrftoken, head):

    r = requests.get('https://www.udemy.com/course/subscribe/?courseId=' + str(courseID), headers=head, verify=False, cookies=cookies)
    
    r2 = requests.get('https://www.udemy.com/api-2.0/users/me/subscribed-courses/' + str(courseID) + '/?fields%5Bcourse%5D=%40default%2Cbuyable_object_type%2Cprimary_subcategory%2Cis_private', headers=head, verify=False, cookies=cookies)
    return r2.json()

def auto_add(list_st, cookies, access_token, csrftoken, head):
    print('\n')
    index = 0
    global count, paid_only
    while index <= len(list_st) - 1:
        sp1 = list_st[index].split('||')
        print(fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fr + str(index + 1), fy + sp1[0], end='')

        link = getRealUrl(sp1[1])
        print(link)
        couponID = get_course_coupon(link)
        course_id = get_course_id(link, cookies)

        if couponID != '' and purchased_text == '':
            slp = ''
            try:
                js = free_checkout(CHECKOUT, access_token, csrftoken, couponID, course_id, cookies, head)

                try:
                    if js['status'] == 'succeeded':
                        print(fg + ' Successfully Enrolled To Course')
                        count += 1
                        index += 1
                except:
                    try:
                        msg = js['detail']
                        print(' ' + fr + msg)
                        slp = int(re.search(r'\d+', msg).group(0))
                        # index -= 1
                    except:
                        print(fr + ' Expired Coupon ' + js['message'])
                        index += 1
                else:
                    try:
                        if js['status'] == 'failed':
                            print(fr + ' Coupon Expired :( ')
                            index += 1
                    except:
                        bnn = ''
            except:
                pass
            if slp != '':
                slp += 10
                print(fc + sd + '----' + fm + sb + '>>' +  fb + ' Pausing execution of script for ' + fr + str(slp) + ' seconds')
                time.sleep(slp)
            else:
                time.sleep(5)

        elif couponID == '' and purchased_text == '':
            if paid_only == False:
                js = free_enroll(course_id, access_token, cookies, csrftoken, head)
                try:
                    if js['_class'] == 'course':
                        print(fg + ' Successfully Subscribed')
                        count += 1
                        index += 1
                except:
                    print(fb + ' COUPON MIGHT HAVE EXPIRED')
                    index += 1
            else:
                print(fg + ' This is a Free Course (Skipped)')
                index += 1
        else:
            print(' ' + fc + purchased_text)
            index += 1
    print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + bc + fw + sb + 'Total Courses Subscribed: ' + str(count))

def process(list_st, dd, limit, site_index, cookies, access_token, csrftoken, head):
    global d
    print('\n')
    for index, stru in enumerate(list_st, start=1):
        sp1 = stru.split('||')
        print(fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fr + str(index), fy + sp1[0])
    print('\n' + fc + sd + '----' + fm + sb + '>>' + fb + ' To load more input "m" OR to subscribe any course from above input "y": ', end='')
    input_2 = input()
    if input_2 == 'm':
        if dd != limit-1:
            return total_sites[site_index + 1]
    elif input_2 == 'y':
        try:
            subs = int(input('\n---->> Enter id of course ex - 1 or 2 or 3.... : '))
        except Exception as e:
            print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fr + 'Enter Correct ID')
            subs = ''
        # print(type(subs))
        if isinstance(subs, int):
            link = list_st[subs-1].split('||')[1]
            couponID = get_course_coupon(link)
            course_id = get_course_id(link, cookies)
            if couponID != '' and purchased_text == '':
                js = free_checkout(CHECKOUT, access_token, csrftoken, couponID, course_id, cookies, head)
                try:
                    if js['status'] == 'succeeded':
                        print(fc + sd + '[' + fm + sb + '*' + fc + sd + '][' + fm + sb + '*' + fc + sd + ']' + fg + ' Successfully Enrolled To Course')
                except:
                    print(js['message'])
            elif couponID == '' and purchased_text == '':
                js = free_enroll(course_id, access_token, cookies, csrftoken, head)
                try:
                    if js['_class'] == 'course':
                        print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '][' + fm + sb + '*' + fc + sd + ']' + fg + ' Successfully Subscribed')
                except:
                    print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + ']' + fr + ' COUPON MIGHT HAVE EXPIRED')
            else:
                print(fc + sd + '[' + fm + sb + '*' + fc + sd + '][' + fm + sb + '*' + fc + sd + ']' + fc + purchased_text)
        d = dd - 1
    else:
        exit()

def fetch_cookies():
    try:
        cookies = browser_cookie3.load(domain_name='www.udemy.com')
        return requests.utils.dict_from_cookiejar(cookies), cookies
    except:
        print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fr + 'Auto login failed!!, try by adding cookie file using "py udemy.py -c cookie_file.txt"')
        exit()

def main():
    sys.stdout.write(banner())
    version = '1.0'
    parser = argparse.ArgumentParser(description='', conflict_handler="resolve")
    general = parser.add_argument_group("General")
    general.add_argument(
        '-h', '--help',\
        action='help',\
        help="Shows the help.")
    general.add_argument(
        '-v', '--version',\
        action='version',\
        version=version,\
        help="Shows the version.")
    authentication = parser.add_argument_group("Authentication")
    authentication.add_argument(
        '-c', '--cookies',\
        dest='cookies',\
        type=str,\
        help="Cookies to authenticate",metavar='')
    
    authentication.add_argument(
        '-k', '--cron',\
        dest='cron',\
        action='store_true',\
        help="Added support to create a cron job/task")

    authentication.add_argument(
        '-p', '--paid',\
        dest='paid',\
        action='store_true',\
        help="Enrol to only paid courses")
    
    try:
        args = parser.parse_args()
        ip = ".".join(map(str, (random.randint(0, 255) 
                                for _ in range(4))))
        global paid_only
        if args.paid:
            paid_only = True
        else:
            paid_only = False
        
        if args.cookies:
            print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fg +'Trying to login with cookies! \n')
            time.sleep(0.8)
            cookies_file = Path(args.cookies)
            if cookies_file.exists():
                fp = open(cookies_file, 'r')
                try:
                    fp_toks = fp.read().split('||')
                    access_token = fp_toks[0]
                    client_id = fp_toks[1]
                    print(fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fg +'Login Successful! \n')
                except Exception as z:
                    print(fr + 'cookie file is not in right format')
                    exit()
                
                csrftoken = ''
                cookies = cookiejar(client_id, access_token)
                head = {
                    'authorization': 'Bearer ' + access_token,
                    'accept': 'application/json, text/plain, */*',
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                    'x-forwarded-for': str(ip),
                    'x-udemy-authorization': 'Bearer ' + access_token,
                    'content-type': 'application/json;charset=UTF-8',
                    'referer': 'https://www.udemy.com/courses/search/?q=free%20courses&src=sac&kw=free',
                    'origin': 'https://www.udemy.com'
                }
            else:
                print(fr + 'Cookie file does not exists')
                exit()
        else:
            my_cookies, cookies = fetch_cookies()
            try:
                access_token = my_cookies['access_token']
                csrftoken = my_cookies['csrftoken']

                head = {
                    'authorization': 'Bearer ' + access_token,
                    'accept': 'application/json, text/plain, */*',
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                    'x-forwarded-for': str(ip),
                    'x-udemy-authorization': 'Bearer ' + access_token,
                    'content-type': 'application/json;charset=UTF-8',
                    'origin': 'https://www.udemy.com',
                    'referer': 'https://www.udemy.com/'
                }
                print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fg +'Auto Login Successful! \n')

            except Exception as e:
                print('\n' + fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fr + 'Make sure you are logged in to udemy.com in chrome browser')
                access_token = ''
        if access_token != '':
            time.sleep(0.8)
            print(fc + sd + '[' + fm + sb + '*' + fc + sd + '] ' + fw + 'Websites Available: ')
            bad_colors = ['BLACK', 'WHITE', 'LIGHTBLACK_EX', 'RESET']
            codes = vars(colorama.Fore)
            colors = [codes[color] for color in codes if color not in bad_colors]
            for site in total_sites:
                print(random.choice(colors) + site)
            
            global count
            count = 0
            for index, items in enumerate(func_list):
                print('\n' + fc + sd + '-------' + fm + sb + '>> ' + fb + total_sites[index] + fm + sb + ' <<' + fc + sd + '-------\n')
                limit = site_range[index]
                for d in range(1, limit):
                    list_st = items(d)
                    auto_add(list_st, cookies, access_token, csrftoken, head)
        else:
            print('Make sure you are logged in to udemy.com in chrome browser')
    except Exception as e :
        print(e)
        exit('\nunknown error')

if __name__ == '__main__':
    main()
