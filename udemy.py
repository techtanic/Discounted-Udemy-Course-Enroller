import json
import logging
import os
import random
import re
import threading
import time
import traceback
#!/usr/bin/python3
import webbrowser
from urllib.parse import parse_qs, urlsplit

import browser_cookie3
import PySimpleGUI as sg
import requests
import urllib3
from bs4 import BeautifulSoup

from pack.base64 import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sg.set_global_icon(icon)
sg.change_look_and_feel('dark')
sg.set_options(button_color=(sg.theme_background_color(), sg.theme_background_color()),border_width=0)

def cookiejar(client_id, access_token):
    cookies = dict(client_id=client_id, access_token=access_token)
    return cookies

def getRealUrl(url):
    path = url.split(".com/")[1]

    return "https://www.udemy.com/" + path

def get_course_id(url):
    r2 = s.get(url, verify=False)
    soup = BeautifulSoup(r2.content, 'html5lib')
    if r2.status_code == 404:
        return ''

    else:
        try:
            courseid = soup.find('body',attrs={"class":"ud-app-loader ud-component--course-landing-page-free-udlite udemy"})['data-clp-course-id']
        except:
            courseid = soup.find('body',attrs={"data-module-id":"course-landing-page/udlite"})['data-clp-course-id']
            #with open("problem.txt","w",encoding="utf-8") as f:
                #f.write(str(soup))
    return courseid

def get_course_coupon(url):
    query = urlsplit(url).query
    params = parse_qs(query)
    try:
        params = {k: v[0] for k, v in params.items()}
        return params['couponCode']
    except:
        return ''

def check_purchased(courseid):
    r = requests.get('https://www.udemy.com/api-2.0/course-landing-components/' + courseid +'/me/?components=purchase',headers=head).json()
    try:
        return r['purchase']['data']['purchase_date']
    except:
        return False

def update_courses():
    while True:
        r = s.get('https://www.udemy.com/api-2.0/users/me/subscribed-courses/',headers=head).json()
        new_menu = [
            ['About', ['Github', 'Discord']],
            [f'Total Courses: {r["count"]}'],
            ]
        main_window['mn'].Update(menu_definition = new_menu)
        time.sleep(6) # So that Udemy's api doesn't get spammed.

def free_checkout(coupon, courseid):
    payload = '{"shopping_cart":{"items":[{"buyableType":"course","buyableId":' + str(courseid) + ',"discountInfo":{"code":"' + coupon + '"},"purchasePrice":{"currency":"' + currency + '","currency_symbol":"","amount":0,"price_string":"Free"},"buyableContext":{"contentLocaleId":null}}]},"payment_info":{"payment_vendor":"Free","payment_method":"free-method"}}'
    
    r = s.post('https://www.udemy.com/payment/checkout-submit/', headers=head, data=payload, verify=False)
    return r.json()

def free_enroll(courseid):

    s.get('https://www.udemy.com/course/subscribe/?courseId=' + str(courseid), headers=head, verify=False)
    
    r2 = s.get('https://www.udemy.com/api-2.0/users/me/subscribed-courses/' + str(courseid) + '/?fields%5Bcourse%5D=%40default%2Cbuyable_object_type%2Cprimary_subcategory%2Cis_private', headers=head, verify=False)
    return r2.json()

def auto_add(list_st):
    index = 0
    global count, paid_only
    while index <= len(list_st) - 1:
        sp1 = list_st[index].split('|:|')
        title = str(index + 1)+' '+sp1[0]
        main_window['out'].print(title+' ',text_color='yellow',end = '')

        link = getRealUrl(sp1[1])
        main_window['out'].print(link,text_color='blue')

        couponID = get_course_coupon(link)
        course_id = get_course_id(link)
        if not course_id:
            main_window['out'].print('This Course link is wrong',text_color='light blue')
            main_window['out'].print()
            index += 1

        else:
            purchased = check_purchased(course_id)

            if not purchased:
                if couponID:
                    slp = ''
                    try:
                        js = free_checkout(couponID, course_id)
                        try:
                            if js['status'] == 'succeeded':
                                main_window['out'].print('Successfully Enrolled To Course',text_color='green')
                                main_window['out'].print()
                                count += 1
                                index += 1
                        except:
                            try:
                                msg = js['detail']
                                main_window['out'].print(f'{msg}',text_color='dark blue')
                                main_window['out'].print()
                                slp = int(re.search(r'\d+', msg).group(0))
                                # index -= 1
                            except:
                                main_window['out'].print('Expired Coupon',text_color='red')
                                main_window['out'].print()
                                index += 1
                        else:
                            try:
                                if js['status'] == 'failed':
                                    main_window['out'].print('Coupon Expired :(',text_color='red')
                                    main_window['out'].print()
                                    index += 1
                            except:
                                pass
                    except:
                        pass
                    if slp != '':
                        slp += 10
                        main_window['out'].print('----' +'>>'+' Pausing execution of script for ' +  str(slp) + ' seconds',text_color='red')
                        time.sleep(slp)
                        main_window['out'].print()
                    else:
                        time.sleep(5)

                elif not couponID:
                    js = free_enroll(course_id)
                    try:
                        if js['_class'] == 'course':
                            main_window['out'].print('Successfully Subscribed',text_color='green')
                            main_window['out'].print()
                            count += 1
                            index += 1
                    except:
                        main_window['out'].print('COUPON MIGHT HAVE EXPIRED',text_color='red')
                        main_window['out'].print()
                        index += 1
                
            if purchased:
                main_window['out'].print(purchased,text_color='light blue')
                main_window['out'].print()
                index += 1
        
    main_window['out'].print('Total Courses Subscribed: ' + str(count),text_color='Green')

def fetch_cookies():
    try:
        cookies = browser_cookie3.load(domain_name='www.udemy.com')
        return requests.utils.dict_from_cookiejar(cookies), cookies
    except:
        print('\nAuto login failed!!, try by adding cookie file using "py udemy.py -c cookie_file.txt"')
        exit()


##########################################

def discudemy():
    global du_links
    du_links = []
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }

    for page in range(1,4):
        r = requests.get('https://www.discudemy.com/all/' + str(page), headers=head, verify=False)
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
                r2 = requests.get(url2, headers=head, verify=False)
                soup1 = BeautifulSoup(r2.content, 'html.parser')
                next = soup1.find('div', 'ui center aligned basic segment')
                url3 = next.a['href']
                r3 = requests.get(url3, headers=head, verify=False)
                soup3 = BeautifulSoup(r3.content, 'html.parser')
                du_links.append(title + '|:|' + soup3.find('div', 'ui segment').a['href'])
    #return du_links

def udemy_freebies():
    global uf_links
    uf_links = []
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    for page in range(1,4):
        r = requests.get('https://www.udemyfreebies.com/free-udemy-courses/' + str(page), headers=head, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        all = soup.find_all('div', 'theme-block')
        for index, items in enumerate(all):
            title = items.img['title']
            url2 = items.a['href']
            r2 = requests.get(url2, headers=head, verify=False)
            soup1 = BeautifulSoup(r2.content, 'html.parser')
            url3 = soup1.find('a', class_ = 'button-icon')['href']
            link = requests.get(url3, verify=False).url
            uf_links.append(title + '|:|' + link)
    #return uf_links

def course_mania():
    global cm_links
    cm_links = []
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Referer': 'https://coursemania.xyz/',
        'Origin': 'https://coursemania.xyz',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    
    r = requests.get('https://api.coursemania.xyz/api/get_courses', headers=head, verify=False)
    js = r.json()
    for items in js:
        title = items['courseName']
        link = items['url']
        if 'www.udemy.com' in link:
            cm_links.append(title + '|:|' + link)
    #return cm_links

###########################


def main1():
    global thread_done
    try:
        global paid_only
        global count
        count = 0
        links_ls =[]
        for index, items in enumerate(func_list):
            main_window['out'].print(sites[index],text_color='white')
            main_window['out'].print('Loading URL..',text_color='white')
            items.start()
        for t in func_list:
            t.join()

        try:
            links_ls += du_links
        except:
            pass
        try:
            links_ls += uf_links
        except:
            pass
        try:
            links_ls += cm_links
        except:
            pass

        auto_add(links_ls)

    except:
        e = traceback.format_exc()
        sg.popup_scrolled(e,title='Unknown Error')

    main_window['col1'].Update(visible = True)
    main_window['col2'].Update(visible = False)



############## MAIN ############# MAIN############## MAIN ############# MAIN ############## MAIN ############# MAIN ###########
menu = [
    ['About', ['Github', 'Discord']]
]

c1 = [
    [sg.Button(key = 'a_login',image_data=auto_login) , sg.T(''), sg.B(key = 'c_login',image_data=cookie_login)],
    ]
c2 = [
    [sg.T('Access Token'), sg.InputText(default_text='',key = 'access_token',size=(20,1),pad=(5,5))],
    [sg.T('Client ID'), sg.InputText(default_text='',key = 'client_id',size=(25,1),pad=(5,5))],
    [sg.B(key='Back',image_data=back),sg.T('                     '),sg.B(key = 'Login',image_data=login)],
    ]

login_layout = [
    [sg.Menu(menu)],
    [sg.Column(c1,key = 'col1'), sg.Column(c2,visible = False, key = 'col2')],
    ]

login_window = sg.Window('Login',login_layout)

ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

while True:
    event, values = login_window.read()
    with open('config.json') as f:
        config = json.load(f)
    if event in (None,):
        login_window.close()
        exit()

    elif event == 'a_login':
        try:

            my_cookies, cookies = fetch_cookies()
            
            try:
                access_token = my_cookies['access_token']
                csrftoken = my_cookies['csrftoken']

                head = {
                    'authorization': 'Bearer ' + access_token,
                    'accept': 'application/json, text/plain, */*',
                    'x-requested-with': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
                    'x-forwarded-for': str(ip),
                    'x-udemy-authorization': 'Bearer ' + access_token,
                    'content-type': 'application/json;charset=UTF-8',
                    'origin': 'https://www.udemy.com',
                    'referer': 'https://www.udemy.com/',
                    'dnt': '1',
                    }
                
                r = requests.get('https://www.udemy.com/api-2.0/contexts/me/?me=True&Config=True', headers = head).json()
                currency = r['Config']['price_country']['currency']
                user = ''
                user = r['me']['display_name']

                s = requests.session()
                s.cookies.update(cookies)

                login_window.close()
                
                break

            except Exception as e:
                sg.popup_auto_close('Make sure you are logged in to udemy.com in chrome browser',title = 'Error',auto_close_duration=5,no_titlebar=True)
                access_token = ''

        except:
            e = traceback.format_exc()
            sg.popup_scrolled(e,title='Unknown Error')
    
    elif event == 'c_login':
        login_window['col1'].update(visible = False)
        login_window['col2'].update(visible = True)

        access_token = config['access_token']
        client_id = config['client_id']
        login_window['access_token'].update(value=access_token)
        login_window['client_id'].update(value=client_id)

    elif event == 'Github':
        webbrowser.open("https://github.com/techtanic/Udemy-Course-Grabber")

    elif event == 'Discord':
        sg.popup_scrolled('TECHTANIC#8090',no_titlebar=True)

    elif event == 'Back':
        login_window['col1'].update(visible = True)
        login_window['col2'].update(visible = False)

    elif event == 'Login':

        access_token = values['access_token']
        client_id = values['client_id']
        config['access_token'] = access_token
        config['client_id'] = client_id

        csrftoken = ''
        cookies = cookiejar(client_id, access_token)
        s = requests.session()
        s.cookies.update(cookies)
        head = {
            'authorization': 'Bearer ' + access_token,
            'accept': 'application/json, text/plain, */*',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
            'x-forwarded-for': str(ip),
            'x-udemy-authorization': 'Bearer ' + access_token,
            'content-type': 'application/json;charset=UTF-8',
            'referer': 'https://www.udemy.com/courses/search/?q=free%20courses&src=sac&kw=free',
            'origin': 'https://www.udemy.com'
            }
        try:
            r = requests.get('https://www.udemy.com/api-2.0/contexts/me/?me=True&Config=True', headers = head).json()
            currency = r['Config']['price_country']['currency']
            user = ''
            user = r['me']['display_name']
            with open('config.json','w') as f:
                json.dump(config,f,indent=4)
            login_window.close()
            break

        except:
            sg.popup_auto_close('Login Unsuccessfull',title = 'Error',auto_close_duration=5,no_titlebar=True)
            access_token = ''


checkbox_lo = [
    [sg.Checkbox('Discudemy',default=True)],
    [sg.Checkbox('Udemy Freebies',default=True)],
    [sg.Checkbox('Course Mania',default=True)],   
    ]

c1 = [
    [sg.Frame('Websites',checkbox_lo,'yellow',border_width = 4,)],
    [sg.Button(key='Start',tooltip='Once started will not stop until completed',image_data=start)],
    ]

c2 = [
    [sg.Text('Output')],
    [sg.Multiline(size=(70, 12),key='out',autoscroll=True,disabled=True)],
    ]

main_lo = [
    [sg.Menu(menu,key='mn',)],
    [sg.Text(f'Logged in as: {user}',key='user_t')],
    [sg.pin(sg.Column(c1,key='col1')),sg.pin(sg.Column(c2,key='col2',visible=False))],
    [sg.Button(key='Exit',image_data=exit_)],
    ]

global main_window
main_window = sg.Window('Udemy Course Grabber', main_lo)
threading.Thread(target=update_courses, daemon=True).start()

while True:
        
    event, values = main_window.read()

    if event in (None, 'Exit'):
        break
    
    elif event == 'Github':
        webbrowser.open("https://github.com/techtanic/Udemy-Course-Grabber")

    elif event == 'Discord':
        webbrowser.open("https://discord.gg/wFsfhJh4Rh")

    elif event == 'Start':

        all_func_list = [
        threading.Thread(target=discudemy, daemon=True),
        threading.Thread(target=udemy_freebies, daemon=True),
        threading.Thread(target=course_mania, daemon=True),
        ]

        all_sites = [
        'Discudemy',
        'Udemy Freebies',
        'Course Mania',
        ]

        func_list = []
        sites = []
        user_dumb = True

        for i in range(0,len(all_sites)):
            if values[i]:
                func_list.append(all_func_list[i])
                sites.append(all_sites[i])
                user_dumb = False

        if user_dumb:
            sg.popup_auto_close(f'Smart Move Human',title = 'Error',auto_close_duration=5,no_titlebar=True)
        if not user_dumb:
            main_window['col1'].update(visible = False)
            main_window['col2'].update(visible = True)
            threading.Thread(target=main1, daemon=True).start()


main_window.close()


