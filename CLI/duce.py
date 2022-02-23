import json
import os
import random
import re
import threading
import time
import traceback
from decimal import Decimal
from urllib.parse import parse_qs, unquote, urlsplit

import cloudscraper
import requests
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

from colors import *

# DUCE-CLI

# Scraper
def discudemy():
    global du_links
    du_links = []
    big_all = []
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36 Edg/89.0.774.77",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }

    for page in range(1, 4):
        r = requests.get("https://www.discudemy.com/all/" + str(page), headers=head)
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all("a", {"class": "card-header"})
        big_all.extend(small_all)
    du_bar = tqdm(total=len(big_all), desc="Discudemy")
    for index, item in enumerate(big_all):
        du_bar.update(1)
        title = item.string
        url = item["href"].split("/")[4]
        r = requests.get("https://www.discudemy.com/go/" + url, headers=head)
        soup = bs(r.content, "html5lib")
        du_links.append(title + "|:|" + soup.find("a", id="couponLink").string)
    du_bar.close()


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
    uf_bar = tqdm(total=len(big_all), desc="Udemy Freebies")

    for index, item in enumerate(big_all):
        uf_bar.update(1)
        title = item.img["alt"]
        link = requests.get(
            "https://www.udemyfreebies.com/out/" + item["href"].split("/")[4]
        ).url
        uf_links.append(title + "|:|" + link)
    uf_bar.close()


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
    tb_bar = tqdm(total=len(big_all), desc="Tutorial Bar")

    for index, item in enumerate(big_all):
        tb_bar.update(1)
        title = item.a.string
        url = item.a["href"]
        r = requests.get(url)
        soup = bs(r.content, "html5lib")
        link = soup.find("a", class_="btn_offer_block re_track_btn")["href"]
        if "www.udemy.com" in link:
            tb_links.append(title + "|:|" + link)
    tb_bar.close()


def real_discount():

    global rd_links
    rd_links = []
    big_all = []

    for page in range(1, 3):
        r = requests.get("https://real.discount/stores/Udemy?page=" + str(page))
        soup = bs(r.content, "html5lib")
        small_all = soup.find_all("div", class_="col-xl-4 col-md-6")
        big_all.extend(small_all)
    rd_bar = tqdm(total=len(big_all), desc="Real Discount")

    for index, item in enumerate(big_all):
        rd_bar.update(1)
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
    rd_bar.close()


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
    cv_bar = tqdm(total=len(small_all), desc="Course Vania")

    for index, item in enumerate(small_all):
        cv_bar.update(1)
        title = item.h5.string
        r = requests.get(item.a["href"])
        soup = bs(r.content, "html5lib")
        cv_links.append(
            title + "|:|" + soup.find("div", {"class": "stm-lms-buy-buttons"}).a["href"]
        )
    cv_bar.close()


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
    idc_bar = tqdm(total=len(big_all), desc="IDownloadCoupons")

    for index, item in enumerate(big_all):
        idc_bar.update(1)
        title = item["aria-label"]
        link = unquote(item["href"])
        if link.startswith("https://ad.admitad.com"):
            link = parse_qs(link)["ulp"][0]
        elif link.startswith("https://click.linksynergy.com"):
            link = parse_qs(link)["murl"][0]
        idc_links.append(title + "|:|" + link)
    idc_bar.close()


def enext() -> list:
    en_links = []
    r = requests.get("https://e-next.in/e/udemycoupons.php")
    soup = bs(r.content, "html5lib")
    big_all = soup.find("div", {"class": "scroll-box"}).find_all("p", {"class": "p2"})
    en_bar = tqdm(total=len(big_all), desc="E-next")
    for i in big_all:
        en_bar.update(1)
        title = i.text[11:].strip().removesuffix("Enroll Now free").strip()
        link = i.a["href"]
        en_links.append(title + "|:|" + link)
    en_bar.close()


# Constants

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
        with open("duce-cli-settings.json") as f:
            settings = json.load(f)

    except FileNotFoundError:
        settings = requests.get(
            "https://raw.githubusercontent.com/techtanic/Discounted-Udemy-Course-Enroller/master/duce-cli-settings.json"
        ).json()

    title_exclude = "\n".join(settings["title_exclude"])
    instructor_exclude = "\n".join(settings["instructor_exclude"])

    try:
        settings["languages"]["Russian"]
    except KeyError:
        settings["languages"]["Russian"] = True
    settings.setdefault("save_txt", True)  # v1.3
    settings["sites"].setdefault("E-next", True)  # v1.4
    settings.setdefault("discounted_only", False)  # v1.4
    return settings, instructor_exclude, title_exclude


def save_settings():
    with open("duce-cli-settings.json", "w") as f:
        json.dump(settings, f, indent=4)


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


def update_available():
    if version.removeprefix("v") < requests.get(
        "https://api.github.com/repos/techtanic/Discounted-Udemy-Course-Enroller/releases/latest"
    ).json()["tag_name"].removeprefix("v"):
        print(by + fr + "  Update Available  ")
    else:
        return


def check_login(email, password):
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
            "email": email,
            "password": password,
        }

        s.headers.update({"Referer": "https://www.udemy.com/join/signup-popup/"})
        try:
            r = s.post(
                "https://www.udemy.com/join/login-popup/?locale=en_US",
                data=data,
                allow_redirects=False,
            )
        except cloudscraper.exceptions.CloudflareChallengeError:
            continue
        if r.status_code == 302:

            cookies = cookiejar(
                r.cookies["client_id"], r.cookies["access_token"], csrf_token
            )

            head = {
                "authorization": "Bearer " + r.cookies["access_token"],
                "accept": "application/json, text/plain, */*",
                "x-requested-with": "XMLHttpRequest",
                "x-forwarded-for": str(
                    ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
                ),
                "x-udemy-authorization": "Bearer " + r.cookies["access_token"],
                "content-type": "application/json;charset=UTF-8",
                "origin": "https://www.udemy.com",
                "referer": "https://www.udemy.com/",
                "dnt": "1",
            }

            s = requests.session()
            s.cookies.update(cookies)
            s.headers.update(head)
            s.keep_alive = False

            r = s.get(
                "https://www.udemy.com/api-2.0/contexts/me/?me=True&Config=True"
            ).json()
            currency = r["Config"]["price_country"]["currency"]
            user = r["me"]["display_name"]
            settings["email"], settings["password"] = email, password
            save_settings()
            return head, user, currency, s, ""

        else:
            soup = bs(r.content, "html5lib")
            txt = soup.find(
                "div", class_="alert alert-danger js-error-alert"
            ).text.strip()
            if txt[0] == "Y":
                return "", "", "", "", "Too many logins per hour try later"
            elif txt[0] == "T":
                return "", "", "", "", "Email or password incorrect"
            else:
                return "", "", "", "", txt

    return (
        "",
        "",
        "",
        "",
        "Cloudflare is blocking your requests try again after an hour",
    )


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

    s.get("https://www.udemy.com/course/subscribe/?courseId=" + str(courseid))

    r = s.get(
        "https://www.udemy.com/api-2.0/users/me/subscribed-courses/"
        + str(courseid)
        + "/?fields%5Bcourse%5D=%40default%2Cbuyable_object_type%2Cprimary_subcategory%2Cis_private"
    )
    return r.json()


# -----------------


def auto(list_st):

    se_c, ae_c, e_c, ex_c, as_c = 0, 0, 0, 0, 0
    if settings["save_txt"]:
        if not os.path.exists("Courses/"):
            os.makedirs("Courses/")
        txt_file = open(f"Courses/" + time.strftime("%Y-%m-%d--%H-%M"), "w")
    for index, combo in enumerate(list_st):

        tl = combo.split("|:|")
        print(fy + str(index) + " " + tl[0], end=" ")
        link = tl[1]
        print(fb + link)
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
                    print(flb + f"Instructor excluded: {instructor}")
                    ex_c += 1
                elif title_in_exclusion(tl[0], title_exclude):
                    print(flb + f"Instructor excluded: {instructor}")
                elif cat not in categories:
                    print(flb + f"Category excluded: {cat}")
                elif lang not in languages:
                    print(flb + f"Languages excluded: {lang}")
                elif avg_rating < min_rating:
                    print(flb + f"Poor rating: {avg_rating}")
                print()
                ex_c += 1

            else:
                if not purchased:

                    if coupon_id:
                        slp = ""

                        js = free_checkout(coupon_id, course_id)
                        try:
                            if js["status"] == "succeeded":
                                print(fg + "Successfully Enrolled\n")
                                se_c += 1
                                as_c += amount
                                if settings["save_txt"]:
                                    txt_file.write(combo + "\n")
                                    txt_file.flush()
                                    os.fsync(txt_file.fileno())

                            elif js["status"] == "failed":
                                # print(js)
                                print(fr + "Coupon Expired\n")
                                e_c += 1

                        except:
                            try:
                                msg = js["detail"]
                                print(fr + msg)
                                print()
                                slp = int(re.search(r"\d+", msg).group(0))
                            except:
                                # print(js)
                                print(fr + "Expired Coupon\n")
                                e_c += 1

                        if slp != "":
                            slp += 5
                            print(
                                fr
                                + ">>> Pausing execution of script for "
                                + str(slp)
                                + " seconds\n",
                            )
                            time.sleep(slp)
                        else:
                            time.sleep(4)

                    elif not coupon_id:
                        js = free_enroll(course_id)
                        try:
                            if js["_class"] == "course":
                                print(fg + "Successfully Subscribed\n")
                                se_c += 1
                                as_c += amount
                                if settings["save_txt"]:
                                    txt_file.write(combo + "\n")
                                    txt_file.flush()
                                    os.fsync(txt_file.fileno())
                        except:
                            print(fr + "COUPON MIGHT HAVE EXPIRED\n")
                            e_c += 1

                elif purchased:
                    print(flb + purchased)
                    print()
                    ae_c += 1

        elif not course_id:
            print(fr + ".Course Expired.\n")
            e_c += 1

        # main_window["pout"].update(index + 1)
    print(f"Successfully Enrolled: {se_c}")
    print(f"Already Enrolled: {ae_c}")
    print(f"Amount Saved: ${round(as_c,2)}")
    print(f"Expired Courses: {e_c}")
    print(f"Excluded Courses: {ex_c}")


def random_color():
    col = ["green", "yellow", "white"]
    return random.choice(col)


##########################################


def main1():
    try:
        links_ls = []
        for index in funcs:
            funcs[index].start()
            time.sleep(0.09)
        for t in funcs:
            funcs[t].join()
        time.sleep(1)

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
        print(e)


settings, instructor_exclude, title_exclude = load_settings()
############## MAIN ############# MAIN############## MAIN ############# MAIN ############## MAIN ############# MAIN ###########

txt = True
while txt:
    if settings["email"] or settings["password"]:
        email, password = settings["email"], settings["password"]
    else:
        email = input("Email: ")
        password = input("Password: ")
    print(fb + "Trying to login")
    head, user, currency, s, txt = check_login(email, password)
    if txt:
        print(fr + txt)

print(fg + f"Logged in as {user}")
try:
    update_available()
except:
    pass

all_functions = create_scrape_obj()
funcs = {}
sites = []
categories = []
languages = []
instructor_exclude = settings["instructor_exclude"]
title_exclude = settings["title_exclude"]
min_rating = settings["min_rating"]
user_dumb = True

for name in settings["sites"]:
    if settings["sites"][name]:
        funcs[name] = all_functions[name]
        sites.append(name)
        user_dumb = False

for cat in settings["categories"]:
    if settings["categories"][cat]:
        categories.append(cat)

for lang in settings["languages"]:
    if settings["languages"][lang]:
        languages.append(lang)

if user_dumb:
    print(bw + fr + "  No sites selected  ")
if not user_dumb:
    tm = threading.Thread(target=main1, daemon=True)
    tm.start()

tm.join()
