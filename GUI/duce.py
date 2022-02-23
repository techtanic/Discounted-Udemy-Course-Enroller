import json
import os
import random
import re
import sys
import threading
import time
import traceback
from decimal import Decimal
from urllib.parse import parse_qs, unquote, urlsplit
from webbrowser import open as web
from pack import browser_cookie3
import cloudscraper
import PySimpleGUI as sg
import requests
from bs4 import BeautifulSoup as bs

from pack.base64 import *

# DUCE

sg.set_global_icon(icon)
sg.change_look_and_feel("dark")
sg.theme_background_color
sg.set_options(
    button_color=(sg.theme_background_color(), sg.theme_background_color()),
    border_width=0,
    font=10,
)

############## Scraper
def discudemy():
    global du_links
    du_links = []
    big_all = []
    head = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }

    for page in range(1, 4):
        r = requests.get("https://www.discudemy.com/all/" + str(page), headers=head)
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all("a", {"class": "card-header"})
        big_all.extend(small_all)
        main_window["pDiscudemy"].update(page)
    main_window["pDiscudemy"].update(0, max=len(big_all))

    for index, item in enumerate(big_all):
        main_window["pDiscudemy"].update(index + 1)

        title = item.string
        url = item["href"].split("/")[4]
        r = requests.get("https://www.discudemy.com/go/" + url, headers=head)
        soup = bs(r.content, "html5lib")
        du_links.append(title + "|:|" + soup.find("a", id="couponLink").string)

    main_window["pDiscudemy"].update(0, visible=False)
    main_window["iDiscudemy"].update(visible=True)


def udemy_freebies():
    global uf_links
    uf_links = []
    big_all = []

    for page in range(1, 3):
        r = requests.get(
            "https://www.udemyfreebies.com/free-udemy-courses/" + str(page)
        )
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all("a", {"class": "theme-img"})
        big_all.extend(small_all)
        main_window["pUdemy Freebies"].update(page)
    main_window["pUdemy Freebies"].update(0, max=len(big_all))

    for index, item in enumerate(big_all):
        main_window["pUdemy Freebies"].update(index + 1)
        title = item.img["alt"]
        link = requests.get(
            "https://www.udemyfreebies.com/out/" + item["href"].split("/")[4]
        ).url
        uf_links.append(title + "|:|" + link)
    main_window["pUdemy Freebies"].update(0, visible=False)
    main_window["iUdemy Freebies"].update(visible=True)


def tutorialbar():

    global tb_links
    tb_links = []
    big_all = []

    for page in range(1, 4):
        r = requests.get("https://www.tutorialbar.com/all-courses/page/" + str(page))
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all(
            "h3", class_="mb15 mt0 font110 mobfont100 fontnormal lineheight20"
        )
        big_all.extend(small_all)
        main_window["pTutorial Bar"].update(page)
    main_window["pTutorial Bar"].update(0, max=len(big_all))

    for index, item in enumerate(big_all):
        main_window["pTutorial Bar"].update(index + 1)
        title = item.a.string
        url = item.a["href"]
        r = requests.get(url)
        soup = bs(r.content, "html5lib")
        link = soup.find("a", class_="btn_offer_block re_track_btn")["href"]
        if "www.udemy.com" in link:
            tb_links.append(title + "|:|" + link)
    main_window["pTutorial Bar"].update(0, visible=False)
    main_window["iTutorial Bar"].update(visible=True)


def real_discount():

    global rd_links
    rd_links = []
    big_all = []

    for page in range(1, 3):
        r = requests.get("https://real.discount/stores/Udemy?page=" + str(page))
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all("div", class_="col-xl-4 col-md-6")
        big_all.extend(small_all)
    main_window["pReal Discount"].update(page)
    main_window["pReal Discount"].update(0, max=len(big_all))

    for index, item in enumerate(big_all):
        main_window["pReal Discount"].update(index + 1)
        title = item.a.h3.string
        url = "https://real.discount" + item.a["href"]
        r = requests.get(url)
        soup = bs(r.content, "html5lib")
        link = soup.find("div", class_="col-xs-12 col-md-12 col-sm-12 text-center").a[
            "href"
        ]
        if link.startswith("http://click.linksynergy.com"):
            link = parse_qs(link)["RD_PARM1"][0]

        rd_links.append(title + "|:|" + link)
    main_window["pReal Discount"].update(0, visible=False)
    main_window["iReal Discount"].update(visible=True)


def coursevania():

    global cv_links
    cv_links = []
    r = requests.get("https://coursevania.com/courses/")
    soup = bs(r.content, "html5lib")

    nonce = json.loads(
        [
            script.string
            for script in soup.find_all("script")
            if script.string and "load_content" in script.string
        ][0].strip("_mlv = norsecat;\n")
    )["load_content"]

    r = requests.get(
        "https://coursevania.com/wp-admin/admin-ajax.php?&template=courses/grid&args={%22posts_per_page%22:%2230%22}&action=stm_lms_load_content&nonce="
        + nonce
        + "&sort=date_high"
    ).json()

    soup = bs(r["content"], "html5lib")
    small_all = soup.find_all("div", {"class": "stm_lms_courses__single--title"})
    main_window["pCourse Vania"].update(0, max=len(small_all))

    for index, item in enumerate(small_all):
        main_window["pCourse Vania"].update(index + 1)
        title = item.h5.string
        r = requests.get(item.a["href"])
        soup = bs(r.content, "html5lib")
        cv_links.append(
            title + "|:|" + soup.find("div", {"class": "stm-lms-buy-buttons"}).a["href"]
        )
    main_window["pCourse Vania"].update(0, visible=False)
    main_window["iCourse Vania"].update(visible=True)


def idcoupons():

    global idc_links
    idc_links = []
    big_all = []
    for page in range(1, 6):
        r = requests.get(
            "https://idownloadcoupon.com/product-category/udemy-2/page/" + str(page)
        )
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all("a", attrs={"class": "button product_type_external"})
        big_all.extend(small_all)
    main_window["pIDownloadCoupons"].update(0, max=len(big_all))

    for index, item in enumerate(big_all):
        main_window["pIDownloadCoupons"].update(index + 1)
        title = item["aria-label"]
        link = unquote(item["href"])
        if link.startswith("https://ad.admitad.com"):
            link = parse_qs(link)["ulp"][0]
        elif link.startswith("https://click.linksynergy.com"):
            link = parse_qs(link)["murl"][0]
        idc_links.append(title + "|:|" + link)
    main_window["pIDownloadCoupons"].update(0, visible=False)
    main_window["iIDownloadCoupons"].update(visible=True)


def enext() -> list:
    en_links = []
    r = requests.get("https://e-next.in/e/udemycoupons.php")
    soup = bs(r.content, "html5lib")
    big_all = soup.find("div", {"class": "scroll-box"}).find_all("p", {"class": "p2"})
    main_window["pE-next"].update(0, max=len(big_all))
    for i in big_all:
        main_window["pE-next"].update(index + 1)
        title = i.text[11:].strip().removesuffix("Enroll Now free").strip()
        link = i.a["href"]
        en_links.append(title + "|:|" + link)
    main_window["pE-next"].update(0, visible=False)
    main_window["iE-next"].update(visible=True)


########################### Constants

version = "v1.7"


def create_scrape_obj():
    funcs = {
        "Discudemy": threading.Thread(target=discudemy, daemon=True),
        "Udemy Freebies": threading.Thread(target=udemy_freebies, daemon=True),
        "Tutorial Bar": threading.Thread(target=tutorialbar, daemon=True),
        "Real Discount": threading.Thread(target=real_discount, daemon=True),
        "Course Vania": threading.Thread(target=coursevania, daemon=True),
        "IDownloadCoupons": threading.Thread(target=idcoupons, daemon=True),
        "E-next": threading.Thread(target=enext, daemon=True),
    }
    return funcs


################
def cookiejar(
    client_id,
    access_token,
    csrf_token,
):
    cookies = dict(
        client_id=client_id,
        access_token=access_token,
        csrf_token=csrf_token,
    )
    return cookies


def load_settings():
    try:
        os.rename("duce-settings.json", "duce-gui-settings.json")
    except:
        pass
    try:
        with open("duce-gui-settings.json") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = dict(
            requests.get(
                "https://raw.githubusercontent.com/techtanic/Discounted-Udemy-Course-Enroller/master/duce-gui-settings.json"
            ).json()
        )

    title_exclude = "\n".join(settings["title_exclude"])
    instructor_exclude = "\n".join(settings["instructor_exclude"])

    settings.setdefault("save_txt", True)  # v1.3
    settings["sites"].setdefault("E-next", True)  # v1.4
    settings.setdefault("discounted_only", False)  # v1.4

    return settings, instructor_exclude, title_exclude


def save_settings():
    with open("duce-gui-settings.json", "w") as f:
        json.dump(settings, f, indent=4)


def fetch_cookies():
    cookies = browser_cookie3.load(domain_name="www.udemy.com")
    return requests.utils.dict_from_cookiejar(cookies), cookies


def get_course_id(url):
    r = requests.get(url, allow_redirects=False)
    if r.status_code in (404, 302, 301):
        return False
    if "/course/draft/" in url:
        return False
    soup = bs(r.content, "html5lib")

    try:
        courseid = soup.find(
            "div",
            attrs={"data-content-group": "Landing Page"},
        )["data-course-id"]
    except:
        courseid = soup.find(
            "body", attrs={"data-module-id": "course-landing-page/udlite"}
        )["data-clp-course-id"]
        # with open("problem.txt","w",encoding="utf-8") as f:
        # f.write(str(soup))
    return courseid


def get_course_coupon(url):
    query = urlsplit(url).query
    params = parse_qs(query)
    try:
        params = {k: v[0] for k, v in params.items()}
        return params["couponCode"]
    except:
        return ""


def affiliate_api(courseid):
    r = s.get(
        "https://www.udemy.com/api-2.0/courses/"
        + courseid
        + "/?fields[course]=locale,primary_category,avg_rating_recent,visible_instructors",
    ).json()

    instructor = (
        r["visible_instructors"][0]["url"].removeprefix("/user/").removesuffix("/")
    )
    return (
        r["primary_category"]["title"],
        r["locale"]["simple_english_title"],
        round(r["avg_rating_recent"], 1),
        instructor,
    )


def course_landing_api(courseid):
    r = s.get(
        "https://www.udemy.com/api-2.0/course-landing-components/"
        + courseid
        + "/me/?components=purchase"
    ).json()

    try:
        purchased = r["purchase"]["data"]["purchase_date"]
    except:
        purchased = False

    try:
        amount = r["purchase"]["data"]["list_price"]["amount"]
    except:
        print(r["purchase"]["data"])
    return purchased, Decimal(amount)


def remove_duplicates(l):
    l = l[::-1]
    for i in l:
        while l.count(i) > 1:
            l.remove(i)
    return l[::-1]


def update_courses():
    while True:
        r = s.get("https://www.udemy.com/api-2.0/users/me/subscribed-courses/").json()
        new_menu = [
            ["Help", ["Support", "Github", "Discord"]],
            [f'Total Courses: {r["count"]}'],
        ]
        main_window["mn"].Update(menu_definition=new_menu)
        time.sleep(10)  # So that Udemy's api doesn't get spammed.


def update_available():
    release_version = requests.get(
        "https://api.github.com/repos/techtanic/Discounted-Udemy-Course-Enroller/releases/latest"
    ).json()["tag_name"]
    if version.removeprefix("v") < release_version.removeprefix("v"):
        return (
            f" Update {release_version} Availabe",
            f"Update {release_version} Availabe",
        )
    else:
        return f"Login {version}", f"Discounted-Udemy-Course-Enroller {version}"


def manual_login():
    for retry in range(0, 2):

        s = cloudscraper.CloudScraper()
        
        r = s.get(
            "https://www.udemy.com/join/signup-popup/",
        )
        soup = bs(r.text, "html5lib")
        
        csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]
        data = {
            "csrfmiddlewaretoken": csrf_token,
            "locale": "en_US",
            "email": settings["email"],
            "password": settings["password"],
        }

        s.headers.update({"Referer": "https://www.udemy.com/join/signup-popup/"})
        r = s.get("https://www.udemy.com/join/login-popup/?locale=en_US")
        try:
            r = s.post(
                "https://www.udemy.com/join/login-popup/?locale=en_US",
                data=data,
                allow_redirects=False,
            )
        except cloudscraper.exceptions.CloudflareChallengeError:
            continue
        if r.status_code == 302:
            return "", r.cookies["client_id"], r.cookies["access_token"], csrf_token
        else:
            soup = bs(r.content, "html5lib")
            with open("test.txt", "w") as f:
                f.write(r.text)
            txt = soup.find(
                "div", class_="alert alert-danger js-error-alert"
            ).text.strip()
            if txt[0] == "Y":
                return "Too many logins per hour try later", "", "", ""
            elif txt[0] == "T":
                return "Email or password incorrect", "", "", ""
            else:
                return txt, "", "", ""

    return "Cloudflare is blocking your requests try again after an hour", "", "", ""


def check_login(client_id, access_token, csrf_token):
    head = {
        "authorization": "Bearer " + access_token,
        "accept": "application/json, text/plain, */*",
        "x-requested-with": "XMLHttpRequest",
        "x-forwarded-for": str(
            ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
        ),
        "x-udemy-authorization": "Bearer " + access_token,
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.udemy.com",
        "referer": "https://www.udemy.com/",
        "dnt": "1",
    }

    r = requests.get(
        "https://www.udemy.com/api-2.0/contexts/me/?me=True&Config=True", headers=head
    ).json()
    currency = r["Config"]["price_country"]["currency"]
    user = r["me"]["display_name"]

    s = requests.session()
    cookies = cookiejar(client_id, access_token, csrf_token)
    s.cookies.update(cookies)
    s.headers.update(head)
    s.keep_alive = False

    return head, user, currency, s


def title_in_exclusion(title, t_x):
    title_words = title.casefold().split()
    for word in title_words:
        word = word.casefold()
        if word in t_x:
            return True
    return False


# -----------------
def free_checkout(coupon, courseid):
    payload = (
        '{"checkout_environment":"Marketplace","checkout_event":"Submit","shopping_info":{"items":[{"discountInfo":{"code":"'
        + coupon
        + '"},"buyable":{"type":"course","id":'
        + str(courseid)
        + ',"context":{}},"price":{"amount":0,"currency":"'
        + currency
        + '"}}]},"payment_info":{"payment_vendor":"Free","payment_method":"free-method"}}'
    )

    r = s.post(
        "https://www.udemy.com/payment/checkout-submit/",
        data=payload,
        verify=False,
    )
    return r.json()


def free_enroll(courseid):

    s.get(
        "https://www.udemy.com/course/subscribe/?courseId=" + str(courseid),
        verify=False,
    )

    r = s.get(
        "https://www.udemy.com/api-2.0/users/me/subscribed-courses/"
        + str(courseid)
        + "/?fields%5Bcourse%5D=%40default%2Cbuyable_object_type%2Cprimary_subcategory%2Cis_private",
        verify=False,
    )
    return r.json()


# -----------------


def auto(list_st):
    main_window["pout"].update(0, max=len(list_st))
    se_c, ae_c, e_c, ex_c, as_c = 0, 0, 0, 0, 0
    if settings["save_txt"]:
        if not os.path.exists("Courses/"):
            os.makedirs("Courses/")
        txt_file = open(f"Courses/" + time.strftime("%Y-%m-%d--%H-%M"), "w")
    for index, combo in enumerate(list_st):
        tl = combo.split("|:|")
        main_window["out"].print(str(index) + " " + tl[0], text_color="yellow", end=" ")
        link = tl[1]
        main_window["out"].print(link, text_color="blue")
        try:
            course_id = get_course_id(link)
            if course_id:
                coupon_id = get_course_coupon(link)
                cat, lang, avg_rating, instructor = affiliate_api(course_id)
                purchased, amount = course_landing_api(course_id)
                if (
                    instructor in instructor_exclude
                    or title_in_exclusion(tl[0], title_exclude)
                    or cat not in categories
                    or lang not in languages
                    or avg_rating < min_rating
                ):
                    if instructor in instructor_exclude:
                        main_window["out"].print(
                            f"Instructor excluded: {instructor}",
                            text_color="light blue",
                        )
                    elif title_in_exclusion(tl[0], title_exclude):
                        main_window["out"].print(
                            "Title Excluded", text_color="light blue"
                        )
                    elif cat not in categories:
                        main_window["out"].print(
                            f"Category excluded: {cat}", text_color="light blue"
                        )
                    elif lang not in languages:
                        main_window["out"].print(
                            f"Languages excluded: {lang}", text_color="light blue"
                        )
                    elif avg_rating < min_rating:
                        main_window["out"].print(
                            f"Poor rating: {avg_rating}", text_color="light blue"
                        )
                    main_window["out"].print()
                    ex_c += 1

                else:

                    if not purchased:

                        if coupon_id:
                            slp = ""

                            js = free_checkout(coupon_id, course_id)
                            try:
                                if js["status"] == "succeeded":
                                    main_window["out"].print(
                                        "Successfully Enrolled To Course :)",
                                        text_color="green",
                                    )
                                    main_window["out"].print()
                                    se_c += 1
                                    as_c += amount
                                    if settings["save_txt"]:
                                        txt_file.write(combo + "\n")
                                        txt_file.flush()
                                        os.fsync(txt_file.fileno())
                                elif js["status"] == "failed":
                                    # print(js)
                                    main_window["out"].print(
                                        "Coupon Expired :(", text_color="red"
                                    )
                                    main_window["out"].print()
                                    e_c += 1

                            except:
                                try:
                                    msg = js["detail"]
                                    main_window["out"].print(
                                        f"{msg}", text_color="dark blue"
                                    )
                                    main_window["out"].print()
                                    print(js)
                                    slp = int(re.search(r"\d+", msg).group(0))
                                except:
                                    # print(js)
                                    main_window["out"].print(
                                        "Expired Coupon", text_color="red"
                                    )
                                    main_window["out"].print()
                                    e_c += 1

                            if slp != "":
                                slp += 3
                                main_window["out"].print(
                                    ">>> Pausing execution of script for "
                                    + str(slp)
                                    + " seconds",
                                    text_color="red",
                                )
                                time.sleep(slp)
                                main_window["out"].print()
                            else:
                                time.sleep(3.5)

                        elif not coupon_id:
                            if settings["discounted_only"]:
                                main_window["out"].print(
                                    "Free course excluded", text_color="light blue"
                                )
                                ex_c += 1
                                continue
                            js = free_enroll(course_id)
                            try:
                                if js["_class"] == "course":
                                    main_window["out"].print(
                                        "Successfully Subscribed", text_color="green"
                                    )
                                    main_window["out"].print()
                                    se_c += 1
                                    as_c += amount

                                    if settings["save_txt"]:
                                        txt_file.write(combo + "\n")
                                        txt_file.flush()
                                        os.fsync(txt_file.fileno())

                            except:
                                main_window["out"].print(
                                    "COUPON MIGHT HAVE EXPIRED", text_color="red"
                                )
                                main_window["out"].print()
                                e_c += 1

                    elif purchased:
                        main_window["out"].print(purchased, text_color="light blue")
                        main_window["out"].print()
                        ae_c += 1

            elif not course_id:
                main_window["out"].print(".Course Expired.", text_color="red")
                e_c += 1
            main_window["pout"].update(index + 1)
        except:
            e = traceback.format_exc()
            print(e)
    main_window["done_col"].update(visible=True)

    main_window["se_c"].update(value=f"Successfully Enrolled: {se_c}")
    main_window["as_c"].update(value=f"Amount Saved: ${round(as_c,2)}")
    main_window["ae_c"].update(value=f"Already Enrolled: {ae_c}")
    main_window["e_c"].update(value=f"Expired Courses: {e_c}")
    main_window["ex_c"].update(value=f"Excluded Courses: {ex_c}")


##########################################


def main1():
    try:
        links_ls = []
        for key in funcs:
            main_window[f"pcol{key}"].update(visible=True)
        main_window["main_col"].update(visible=False)
        main_window["scrape_col"].update(visible=True)
        for key in funcs:
            funcs[key].start()
        for t in funcs:
            funcs[t].join()
        main_window["scrape_col"].update(visible=False)
        main_window["output_col"].update(visible=True)

        for link_list in [
            "du_links",
            "uf_links",
            "tb_links",
            "rd_links",
            "cv_links",
            "idc_links",
            "en_links",
        ]:
            try:
                links_ls += eval(link_list)
            except:
                pass

        auto(remove_duplicates(links_ls))

    except:
        e = traceback.format_exc()
        sg.popup_scrolled(e, title=f"Unknown Error {version}")

    main_window["output_col"].Update(visible=False)


settings, instructor_exclude, title_exclude = load_settings()
login_title, main_title = update_available()


############## MAIN ############# MAIN############## MAIN ############# MAIN ############## MAIN ############# MAIN ###########
menu = [["Help", ["Support", "Github", "Discord"]]]

login_error = False
try:
    if settings["stay_logged_in"]["auto"]:
        my_cookies, cookies = fetch_cookies()
        head, user, currency, s = check_login(
            my_cookies["client_id"], my_cookies["access_token"], my_cookies["csrftoken"]
        )

    elif settings["stay_logged_in"]["manual"]:
        txt, client_id, access_token, csrf_token = manual_login()
        if not txt:
            head, user, currency, s = check_login(client_id, access_token, csrf_token)

except:
    login_error = True
if (
    not settings["stay_logged_in"]["auto"] and not settings["stay_logged_in"]["manual"]
) or login_error:

    c1 = [
        [
            sg.Button(key="a_login", image_data=auto_login),
            sg.T(""),
            sg.B(key="m_login", image_data=manual_login_),
        ],
        [
            sg.Checkbox(
                "Stay logged-in",
                default=settings["stay_logged_in"]["auto"],
                key="sli_a",
            )
        ],
    ]
    c2 = [
        [
            sg.T("Email"),
            sg.InputText(
                default_text=settings["email"], key="email", size=(20, 1), pad=(5, 5)
            ),
        ],
        [
            sg.T("Password"),
            sg.InputText(
                default_text=settings["password"],
                key="password",
                size=(20, 1),
                pad=(5, 5),
                password_char="*",
            ),
        ],
        [
            sg.Checkbox(
                "Stay logged-in",
                default=settings["stay_logged_in"]["manual"],
                key="sli_m",
            )
        ],
        [
            sg.B(key="Back", image_data=back),
            sg.T("                     "),
            sg.B(key="Login", image_data=login),
        ],
    ]

    login_layout = [
        [sg.Menu(menu)],
        [sg.Column(c1, key="col1"), sg.Column(c2, visible=False, key="col2")],
    ]

    login_window = sg.Window(login_title, login_layout)

    while True:
        event, values = login_window.read()

        if event in (None,):
            login_window.close()
            sys.exit()

        elif event == "a_login":
            try:
                my_cookies, cookies = fetch_cookies()
                try:
                    head, user, currency, s = check_login(
                        my_cookies["client_id"],
                        my_cookies["access_token"],
                        my_cookies["csrftoken"],
                    )
                    settings["stay_logged_in"]["auto"] = values["sli_a"]
                    save_settings()
                    login_window.close()
                    break

                except Exception as e:
                    
                    e = traceback.format_exc()
                    print(e)
                    sg.popup_auto_close(
                        "Make sure you are logged in to udemy.com in chrome browser",
                        title="Error",
                        auto_close_duration=5,
                        no_titlebar=True,
                    )

            except Exception as e:
                e = traceback.format_exc()
                sg.popup_scrolled(e, title=f"Unknown Error {version}")

        elif event == "m_login":
            login_window["col1"].update(visible=False)
            login_window["col2"].update(visible=True)

            login_window["email"].update(value=settings["email"])
            login_window["password"].update(value=settings["password"])

        elif event == "Github":
            web("https://github.com/techtanic/Discounted-Udemy-Course-Enroller")

        elif event == "Support":
            web("https://techtanic.github.io/duce/")

        elif event == "Discord":
            web("https://discord.gg/wFsfhJh4Rh")

        elif event == "Back":
            login_window["col1"].update(visible=True)
            login_window["col2"].update(visible=False)

        elif event == "Login":

            settings["email"] = values["email"]
            settings["password"] = values["password"]
            try:
                txt, client_id, access_token, csrf_token = manual_login()
                if not txt:
                    head, user, currency, s = check_login(
                        client_id, access_token, csrf_token
                    )
                    settings["stay_logged_in"]["manual"] = values["sli_m"]
                    save_settings()
                    login_window.close()
                    break
                else:
                    sg.popup_auto_close(
                        txt,
                        title="Error",
                        auto_close_duration=5,
                        no_titlebar=True,
                    )

            except:
                e = traceback.format_exc()
                sg.popup_scrolled(e, title=f"Unknown Error {version}")

checkbox_lo = []
for key in settings["sites"]:
    checkbox_lo.append([sg.Checkbox(key, key=key, default=settings["sites"][key])])

categories_lo = []
categories_k = list(settings["categories"].keys())
categories_v = list(settings["categories"].values())
for index, _ in enumerate(settings["categories"]):
    if index % 3 == 0:
        try:
            categories_lo.append(
                [
                    sg.Checkbox(
                        categories_k[index],
                        default=categories_v[index],
                        key=categories_k[index],
                        size=(16, 1),
                    ),
                    sg.Checkbox(
                        categories_k[index + 1],
                        default=categories_v[index + 1],
                        key=categories_k[index + 1],
                        size=(16, 1),
                    ),
                    sg.Checkbox(
                        categories_k[index + 2],
                        default=categories_v[index + 2],
                        key=categories_k[index + 2],
                        size=(15, 1),
                    ),
                ]
            )
        except:
            categories_lo.append(
                [
                    sg.Checkbox(
                        categories_k[index],
                        default=categories_v[index],
                        key=categories_k[index],
                        size=(17, 1),
                    )
                ]
            )

languages_lo = []
languages_k = list(settings["languages"].keys())
languages_v = list(settings["languages"].values())
for index, _ in enumerate(settings["languages"]):
    if index % 3 == 0:
        try:
            languages_lo.append(
                [
                    sg.Checkbox(
                        languages_k[index],
                        default=languages_v[index],
                        key=languages_k[index],
                        size=(8, 1),
                    ),
                    sg.Checkbox(
                        languages_k[index + 1],
                        default=languages_v[index + 1],
                        key=languages_k[index + 1],
                        size=(8, 1),
                    ),
                    sg.Checkbox(
                        languages_k[index + 2],
                        default=languages_v[index + 2],
                        key=languages_k[index + 2],
                        size=(8, 1),
                    ),
                ]
            )
        except IndexError:
            languages_lo.append(
                [
                    sg.Checkbox(
                        languages_k[index],
                        default=languages_v[index],
                        key=languages_k[index],
                        size=(8, 1),
                    ),
                    sg.Checkbox(
                        languages_k[index + 1],
                        default=languages_v[index + 1],
                        key=languages_k[index + 1],
                        size=(8, 1),
                    ),
                ]
            )

main_tab = [
    [
        sg.Frame(
            "Websites",
            checkbox_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            key="fcb",
        ),
        sg.Frame(
            "Language",
            languages_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            key="fl",
        ),
    ],
    [
        sg.Frame(
            "Category",
            categories_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            key="fc",
        )
    ],
]

instructor_ex_lo = [
    [
        sg.Multiline(
            default_text=instructor_exclude, key="instructor_exclude", size=(15, 10)
        )
    ],
    [sg.Text("Paste instructor(s)\nusername in new lines")],
]
title_ex_lo = [
    [sg.Multiline(default_text=title_exclude, key="title_exclude", size=(20, 10))],
    [sg.Text("Keywords in new lines\nNot cAsE sensitive")],
]

rating_lo = [
    [
        sg.Spin(
            [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
            initial_value=settings["min_rating"],
            key="min_rating",
            font=25,
        ),
        sg.Text("0.0 <-> 5.0", font=15),
    ]
]

advanced_tab = [
    [
        sg.Frame(
            "Exclude Instructor",
            instructor_ex_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            font=25,
        ),
        sg.Frame(
            "Title Keyword Exclusion",
            title_ex_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            font=25,
        ),
    ],
    [
        sg.Frame(
            "Minimum Rating",
            rating_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            key="f_min_rating",
            font=25,
        )
    ],
    [
        sg.Checkbox(
            "Save enrolled courses in txt", key="save_txt", default=settings["save_txt"]
        )
    ],
    [
        sg.Checkbox(
            "Enroll in Discounted courses only",
            key="discounted_only",
            default=settings["discounted_only"],
        )
    ],
]


scrape_col = []
for key in settings["sites"]:
    scrape_col.append(
        [
            sg.pin(
                sg.Column(
                    [
                        [
                            sg.Text(key, size=(12, 1)),
                            sg.ProgressBar(
                                3,
                                orientation="h",
                                key=f"p{key}",
                                bar_color=("#1c6fba", "#000000"),
                                border_width=1,
                                size=(20, 20),
                            ),
                            sg.Image(data=check_mark, visible=False, key=f"i{key}"),
                        ]
                    ],
                    key=f"pcol{key}",
                    visible=False,
                )
            )
        ]
    )

output_col = [
    [sg.Text("Output")],
    [sg.Multiline(size=(69, 12), key="out", autoscroll=True, disabled=True)],
    [
        sg.ProgressBar(
            3,
            orientation="h",
            key="pout",
            bar_color=("#1c6fba", "#000000"),
            border_width=1,
            size=(46, 20),
        )
    ],
]

done_col = [
    [sg.Text("       Stats", text_color="#FFD700")],
    [
        sg.Text(
            "Successfully Enrolled:             ",
            key="se_c",
            text_color="#7CFC00",
        )
    ],
    [
        sg.Text(
            "Amount Saved: $                                         ",
            key="as_c",
            text_color="#00FA9A",
        )
    ],
    [sg.Text("Already Enrolled:              ", key="ae_c", text_color="#00FFFF")],
    [sg.Text("Expired Courses:           ", key="e_c", text_color="#FF0000")],
    [sg.Text("Excluded Courses:          ", key="ex_c", text_color="#FF4500")],
]

main_col = [
    [
        sg.TabGroup(
            [[sg.Tab("Main", main_tab), sg.Tab("Advanced", advanced_tab)]],
            border_width=2,
            font=25,
        )
    ],
    [
        sg.Button(
            key="Start",
            tooltip="Once started will not stop until completed",
            image_data=start,
        )
    ],
]

if settings["stay_logged_in"]["auto"] or settings["stay_logged_in"]["manual"]:
    logout_btn_lo = sg.Button(key="Logout", image_data=logout)
else:
    logout_btn_lo = sg.Button(key="Logout", image_data=logout, visible=False)

main_lo = [
    [
        sg.Menu(
            menu,
            key="mn",
        )
    ],
    [sg.Text(f"Logged in as: {user}", key="user_t"), logout_btn_lo],
    [
        sg.pin(sg.Column(main_col, key="main_col")),
        sg.pin(sg.Column(output_col, key="output_col", visible=False)),
        sg.pin(sg.Column(scrape_col, key="scrape_col", visible=False)),
        sg.pin(sg.Column(done_col, key="done_col", visible=False)),
    ],
    [sg.Button(key="Exit", image_data=exit_)],
]

# ,sg.Button(key='Dummy',image_data=back)

global main_window
main_window = sg.Window(main_title, main_lo, finalize=True)
threading.Thread(target=update_courses, daemon=True).start()
update_available()
while True:

    event, values = main_window.read()
    if event == "Dummy":
        print(values)

    if event in (None, "Exit"):
        break

    elif event == "Logout":
        settings["stay_logged_in"]["auto"], settings["stay_logged_in"]["manual"] = (
            False,
            False,
        )
        save_settings()
        break

    elif event == "Support":
        web("https://techtanic.github.io/duce/support/#")

    elif event == "Github":
        web("https://github.com/techtanic/Discounted-Udemy-Course-Enroller")

    elif event == "Discord":
        web("https://discord.gg/wFsfhJh4Rh")

    elif event == "Start":

        for key in settings["languages"]:
            settings["languages"][key] = values[key]
        for key in settings["categories"]:
            settings["categories"][key] = values[key]
        for key in settings["sites"]:
            settings["sites"][key] = values[key]
        settings["instructor_exclude"] = values["instructor_exclude"].split()
        settings["title_exclude"] = list(
            filter(None, values["title_exclude"].split("\n"))
        )
        settings["min_rating"] = float(values["min_rating"])
        settings["save_txt"] = values["save_txt"]
        settings["discounted_only"] = values["discounted_only"]
        save_settings()

        all_functions = create_scrape_obj()
        funcs = {}
        sites = {}
        categories = []
        languages = []
        instructor_exclude = settings["instructor_exclude"]
        title_exclude = settings["title_exclude"]
        min_rating = settings["min_rating"]
        user_dumb = True

        for key in settings["sites"]:
            if values[key]:
                funcs[key] = all_functions[key]
                sites[key] = settings["sites"][key]
                user_dumb = False

        for key in settings["categories"]:
            if values[key]:
                categories.append(key)

        for key in settings["languages"]:
            if values[key]:
                languages.append(key)

        if user_dumb:
            sg.popup_auto_close(
                "What do you even expect to happen!",
                auto_close_duration=5,
                no_titlebar=True,
            )
        if not user_dumb:
            # for key in all_functions:
            # main_window[f"p{key}"].update(0, visible=True)
            # main_window[f"img{index}"].update(visible=False)
            # main_window[f"pcol{index}"].update(visible=False)
            threading.Thread(target=main1, daemon=True).start()

main_window.close()
