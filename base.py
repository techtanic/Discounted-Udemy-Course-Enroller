import json
import os
import random
import re
import threading
import time
import traceback
from decimal import Decimal
from urllib.parse import parse_qs, unquote, urlsplit, urlparse

import browser_cookie3
import cloudscraper
import requests
from bs4 import BeautifulSoup as bs

from colors import *

VERSION = "v2.1"


scraper_dict: dict = {
    "Udemy Freebies": "uf",
    "Tutorial Bar": "tb",
    "Real Discount": "rd",
    "Course Vania": "cv",
    "IDownloadCoupons": "idc",
    "E-next": "en",
    "Discudemy": "du",
}

LINKS = {
    "github": "https://github.com/techtanic/Discounted-Udemy-Course-Enroller",
    "support": "https://techtanic.github.io/duce/support",
    "discord": "https://discord.gg/wFsfhJh4Rh",
}


class LoginException(Exception):
    """Login Error

    Args:
        Exception (str): Exception Reason
    """

    pass


class RaisingThread(threading.Thread):
    def run(self):
        self._exc = None
        try:
            super().run()
        except Exception as e:
            self._exc = e

    def join(self, timeout=None):
        super().join(timeout=timeout)
        if self._exc:
            raise self._exc

class Scraper:
    """
    Scrapers: DU, UF, TB, RD, CV, IDC, EN
    """

    def __init__(self, site_to_scrape: list):
        self.sites = site_to_scrape
        for site in self.sites:
            code_name = scraper_dict[site]
            setattr(self, f"{code_name}_length", 0)
            setattr(self, f"{code_name}_links", [])
            setattr(self, f"{code_name}_done", False)
            setattr(self, f"{code_name}_progress", 0)

    def get_scraped_courses(self, target: object):
        threads = []
        scraped_links = []
        for site in self.sites:
            t = threading.Thread(target=target, args=(site,), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(0.5)
        for t in threads:
            t.join()
        for site in self.sites:
            scraped_links += getattr(self, f"{scraper_dict[site]}_links")
        return scraped_links

    def du(self):
        try:
            big_all = []
            head = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            }

            for page in range(1, 4):
                r = requests.get(f"https://www.discudemy.com/all/{page}", headers=head)
                soup = bs(r.content, "html5lib")
                small_all = soup.find_all("a", {"class": "card-header"})
                big_all.extend(small_all)
            self.du_length = len(big_all)

            pattern = re.compile(r'https:\/\/www\.udemy\.com\/course\/[a-zA-Z0-9\-]+\/\?couponCode=[a-zA-Z0-9]+')
            
            for index, item in enumerate(big_all):
                self.du_progress = index
                title = item.string
                url = item["href"].split("/")[-1]
                for _ in range(2):
                    try:
                        r = requests.get(f"https://www.discudemy.com/go/{url}", headers=head)
                        soup = bs(r.content, "html5lib")
                        self.du_links.append(title + "|:|" + soup.find('a', href=pattern).string)
                        break
                    except:
                        continue

        except Exception:
            self.du_error = traceback.format_exc()
            self.du_length = -1
        self.du_done = True

    def uf(self):
        try:
            big_all = []

            for page in range(1, 3):
                r = requests.get(f"https://www.udemyfreebies.com/free-udemy-courses/{page}")
                soup = bs(r.content, "html5lib")
                small_all = soup.find_all("a", {"class": "theme-img"})
                big_all.extend(small_all)
            self.uf_length = len(big_all)

            for index, item in enumerate(big_all):
                self.uf_progress = index
                title = item.img["alt"]
                for _ in range(2):
                    try:
                        link = requests.get(f"https://www.udemyfreebies.com/out/{item['href'].split('/')[4]}").url
                        self.uf_links.append(title + "|:|" + link)
                        break
                    except:
                        continue

        except Exception:
            self.uf_error = traceback.format_exc()
            self.uf_length = -1
        self.uf_done = True

    def tb(self):
        try:
            big_all = []

            for page in range(1, 4):
                r = requests.get(f"https://www.tutorialbar.com/all-courses/page/{page}")
                soup = bs(r.content, "html5lib")
                small_all = soup.find_all("h3", class_="mb15 mt0 font110 mobfont100 fontnormal lineheight20")
                big_all.extend(small_all)
            self.tb_length = len(big_all)

            for index, item in enumerate(big_all):
                self.tb_progress = index
                title = item.a.string
                url = item.a["href"]
                for _ in range(2):
                    try:
                        r = requests.get(url)
                        soup = bs(r.content, "html5lib")
                        link = soup.find("a", class_="btn_offer_block re_track_btn")["href"]
                        if "www.udemy.com" in link:
                            self.tb_links.append(title + "|:|" + link)
                        break
                    except:
                        continue

        except Exception:
            self.tb_error = traceback.format_exc()
            self.tb_length = -1
        self.tb_done = True

    def rd(self):
        try:
            big_all = []

            headers = {
                "User-Agent": "PostmanRuntime/7.30.0",
                "Host": "www.real.discount",
                "Connection": "Keep-Alive",
            }

            url = "https://www.real.discount/api-web/all-courses/?store=Udemy&page=1&per_page=40&orderby=date&free=1&editorschoices=0"

            try:
                r = requests.get(url, headers=headers, timeout=10)
                r.raise_for_status()
                data = r.json()
            except requests.RequestException as e:
                self.rd_length = -1
                self.rd_done = True
                return

            if 'results' not in data:
                self.rd_length = -1
                self.rd_done = True
                return

            big_all.extend(data["results"])
            self.rd_length = len(big_all)
            self.rd_progress = 0  # Initialize progress

            for index, item in enumerate(big_all):
                title = item.get("name", "No title")
                link = item.get("url", "")

                if link.startswith("https://click.linksynergy.com"):
                    if "murl=" in link:
                        link = link.split("murl=")[1]
                    else:
                        parsed_url = urlparse(link)
                        query_params = parse_qs(parsed_url.query)
                        if "RD_PARM1" in query_params:
                            link = query_params["RD_PARM1"][0]
                        else:
                            continue  # Skip this iteration if no valid link is found

                self.rd_links.append(title + "|:|" + link)
                self.rd_progress = index + 1  # Update progress correctly

        except Exception:
            self.rd_length = -1
        self.rd_done = True

    def cv(self):
        try:
            r = requests.get("https://coursevania.com/courses/")
            soup = bs(r.content, "html5lib")
            script_contents = [
                script.string
                for script in soup.find_all("script")
                if script.string and "load_content" in script.string
            ]
            if script_contents:
                script_content = script_contents[0]
                json_str = script_content.strip().split('=', 1)[1].strip().strip(';')
                nonce_data = json.loads(json_str)
                nonce = nonce_data["load_content"]
            else:
                return

            r = requests.get(
                "https://coursevania.com/wp-admin/admin-ajax.php?&template=courses/grid&args={%22posts_per_page%22:%2260%22}&action=stm_lms_load_content&nonce="
                + nonce
                + "&sort=date_high"
            ).json()

            soup = bs(r["content"], "html5lib")
            small_all = soup.find_all("div", {"class": "stm_lms_courses__single--title"})
            self.cv_length = len(small_all)

            pattern = re.compile(r'https:\/\/www\.udemy\.com\/course\/[a-zA-Z0-9\-]+\/\?couponCode=[a-zA-Z0-9]+')
            for index, item in enumerate(small_all):
                self.cv_progress = index
                title = item.h5.string
                for _ in range(2):
                    try:
                        r = requests.get(item.a["href"])
                        soup = bs(r.content, "html5lib")
                        self.cv_links.append(title + "|:|" + soup.find('a', class_="masterstudy-button-affiliate__link", href=pattern).get('href'))
                        break
                    except:
                        continue

        except Exception:
            self.cv_error = traceback.format_exc()
            self.cv_length = -1
        self.cv_done = True

    def idc(self):
        try:
            big_all = []
            for page in range(1, 6):
                r = requests.get(f"https://idownloadcoupon.com/page/{page}")
                soup = bs(r.content, "html5lib")
                small_all = soup.find_all("a", attrs={"class": "button product_type_external"})
                big_all.extend(small_all)
            self.idc_length = len(big_all)
            self.idc_links = []
            for index, item in enumerate(big_all):
                self.idc_progress = index
                title = item["aria-label"][5:][:-1].strip()
                for _ in range(2):
                    try:
                        r = requests.get(item["href"], allow_redirects=False)
                        link = unquote(r.headers["Location"])
                        if link.startswith("https://click.linksynergy.com"):
                            link = link.split("murl=")[1]
                        self.idc_links.append(title + "|:|" + link)
                        break
                    except:
                        continue

        except Exception:
            self.idc_error = traceback.format_exc()
            self.idc_length = -1
        self.idc_done = True

    def en(self):
        try:
            r = requests.get("https://jobs.e-next.in/public/assets/data/udemy.json").json()
            big_all = r
            self.en_length = len(big_all)
            for index, item in enumerate(big_all):
                self.en_progress = index
                title = item["title"]
                for _ in range(2):
                    try:
                        link = f"https://www.udemy.com/course/{item['url']}/?couponCode={item['code']}"
                        self.en_links.append(title + "|:|" + link)
                        break
                    except:
                        continue

        except Exception:
            self.en_error = traceback.format_exc()
            self.en_length = -1
        self.en_done = True


class Udemy:
    def __init__(self, interface: str):
        self.interface = interface
        self.client = cloudscraper.CloudScraper()

    def print(self, content: str, color: str, **kargs):
        colours_dict = {
            "yellow": fy,
            "red": fr,
            "blue": fb,
            "light blue": flb,
            "green": fg,
        }
        if self.interface == "gui":
            self.window["out"].print(content, text_color=color, **kargs)
        else:
            print(colours_dict[color] + content, **kargs)

    def load_settings(self):
        try:
            with open(f"duce-{self.interface}-settings.json") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = dict(
                requests.get(
                    f"https://raw.githubusercontent.com/techtanic/Discounted-Udemy-Course-Enroller/master/duce-{self.interface}-settings.json"
                ).json()
            )
        if "Nepali" not in self.settings["languages"]:
            self.settings["languages"]["Nepali"] = True  # v1.9
        if "Urdu" not in self.settings["languages"]:
            self.settings["languages"]["Urdu"] = True  # v1.9
        self.settings["languages"] = dict(
            sorted(self.settings["languages"].items(), key=lambda item: item[0])
        )
        self.save_settings()
        self.title_exclude = "\n".join(self.settings["title_exclude"])
        self.instructor_exclude = "\n".join(self.settings["instructor_exclude"])

    def save_settings(self):
        with open(f"duce-{self.interface}-settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def make_cookies(self, client_id: str, access_token: str, csrf_token: str):
        self.cookie_dict = dict(
            client_id=client_id,
            access_token=access_token,
            csrf_token=csrf_token,
        )

    def fetch_cookies(self):
        """Gets cookies from browser
        Sets cookies_dict, cookie_jar
        """
        cookies = browser_cookie3.load(domain_name="www.udemy.com")
        self.cookie_dict: dict = requests.utils.dict_from_cookiejar(cookies)
        self.cookie_jar = cookies

    def get_course_id(self, url: str):
        # url="https://www.udemy.com/course/numpy-and-pandas-for-beginners?couponCode=EBEA9308D6497E4A8326"
        try: 
            r = cloudscraper.CloudScraper().get(url)
        except requests.exceptions.ConnectionError:
            return "retry", url
        soup = bs(r.content, "html5lib")
        try:
            course_id = (
                soup.find("meta", {"property": "og:image"})["content"]
                .split("/")[5]
                .split("_")[0]
            )
        except TypeError:
            course_id = "retry"
        except IndexError:
            course_id = ""
        return course_id, r.url

    def extract_course_coupon(self, url: str) -> bool | str:
        """Get coupon code from url
        Returns:
           False | Coupon code
        """
        query = urlsplit(url).query
        params = parse_qs(query)
        try:
            params = {k: v[0] for k, v in params.items()}
            return params["couponCode"]
        except KeyError:
            return False

    def is_excluded(self, courseid: str, title: str) -> bool:
        r = self.client.get(
            "https://www.udemy.com/api-2.0/courses/"
            + courseid
            + "/?fields[course]=locale,primary_category,avg_rating_recent,visible_instructors",
        ).json()
        try:
            instructor: str = (
                r["visible_instructors"][0]["url"]
                .removeprefix("/user/")
                .removesuffix("/")
            )
        except:
            return "0"
        cat: str = r["primary_category"]["title"]
        lang: str = r["locale"]["simple_english_title"]
        avg_rating: float = round(r["avg_rating_recent"], 1)

        if (
            instructor in self.instructor_exclude
            or self.keyword_exclusion(title)
            or cat not in self.categories
            or lang not in self.languages
            or avg_rating < self.min_rating
        ):
            if instructor in self.instructor_exclude:
                self.print(
                    f"Instructor excluded: {instructor}",
                    color="light blue",
                )
            elif self.keyword_exclusion(title):
                self.print("Keyword Excluded", color="light blue")
            elif cat not in self.categories:
                self.print(f"Category excluded: {cat}", color="light blue")
            elif lang not in self.languages:
                self.print(f"Language excluded: {lang}", color="light blue")
            elif avg_rating < self.min_rating:
                self.print(f"Low rating: {avg_rating}", color="light blue")
            self.print("\n", color="yellow")
            return True
        else:
            return False

    def check_course(
        self, course_id, coupon_id=False
    ) -> tuple[str | bool, Decimal, bool | str]:
        """Checks Purchase,Coupon,Price

        Returns:
            purchased (str | False),
            amount (Decimal)),
            coupon_valid (bool),
        """
        url = f"https://www.udemy.com/api-2.0/course-landing-components/{course_id}/me/?components=purchase"

        if coupon_id:
            url += f",redeem_coupon&couponCode={coupon_id}"

        r = self.client.get(url).json()

        try:
            purchased = r["purchase"]["data"]["purchase_date"]
        except KeyError:
            purchased = "retry"  # rate limit maybe dk
        try:
            amount = r["purchase"]["data"]["list_price"]["amount"]
        except KeyError:
            print(r)
            amount = 0
        coupon_valid = False
        if "redeem_coupon" not in r:
            coupon_id = False
        if coupon_id:
            if r["redeem_coupon"]["discount_attempts"][0]["status"] == "applied":
                coupon_valid = True

        return purchased, Decimal(amount), coupon_valid, coupon_id

    def remove_duplicates(self):
        self.d_c = 0
        l = self.scraped_links[::-1]
        for i in l:
            while l.count(i) > 1:
                l.remove(i)
                self.d_c += 1
        self.scraped_links = l[::-1]

    def check_for_update(self) -> tuple[str, str]:
        r_version = (
            requests.get(
                "https://api.github.com/repos/techtanic/Discounted-Udemy-Course-Enroller/releases/latest"
            )
            .json()["tag_name"]
            .removeprefix("v")
        )
        c_version = VERSION.removeprefix("v")
        if c_version < r_version:
            return (
                f" Update {r_version} Available",
                f"Update {r_version} Available",
            )
        elif c_version == r_version:
            return f"Login {c_version}", f"Discounted-Udemy-Course-Enroller {c_version}"
        else:
            return (
                f"Dev Login {c_version}",
                f"Dev Discounted-Udemy-Course-Enroller {c_version}",
            )

    def manual_login(self, email: str, password: str):

        # s = cloudscraper.CloudScraper()

        s = requests.session()
        r = s.get(
            "https://www.udemy.com/join/signup-popup/",
            headers={"User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)"},
        )

        csrf_token = r.cookies["csrftoken"]

        data = {
            "csrfmiddlewaretoken": csrf_token,
            "locale": "en_US",
            "email": email,
            "password": password,
        }

        # ss = requests.session()
        s.cookies.update(r.cookies)
        s.headers.update(
            {
                "User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-GB,en;q=0.5",
                "Referer": "https://www.udemy.com/join/login-popup/?locale=en_US&response_type=html&next=https%3A%2F%2Fwww.udemy.com%2F",
                "Origin": "https://www.udemy.com",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            }
        )
        # r = s.get("https://www.udemy.com/join/login-popup/?response_type=json")
        s = cloudscraper.create_scraper(sess=s)
        r = s.post(
            "https://www.udemy.com/join/login-popup/?response_type=json",
            data=data,
            allow_redirects=False,
        )
        if r.text.__contains__("returnUrl"):
            self.make_cookies(
                r.cookies["client_id"], r.cookies["access_token"], csrf_token
            )
        else:
            login_error = r.json()["error"]["data"]["formErrors"][0]
            if login_error[0] == "Y":
                raise LoginException("Too many logins per hour try later")
            elif login_error[0] == "T":
                raise LoginException("Email or password incorrect")
            else:
                raise LoginException(login_error)

    def get_session_info(self):
        """Get Session info
        Sets Client Session, currency and name
        """
        s = cloudscraper.CloudScraper()
        # headers = {
        #     "authorization": "Bearer " + self.cookie_dict["access_token"],
        #     "accept": "application/json, text/plain, */*",
        #     "x-requested-with": "XMLHttpRequest",
        #     "x-forwarded-for": str(
        #         ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
        #     ),
        #     "x-udemy-authorization": "Bearer " + self.cookie_dict["access_token"],
        #     "content-type": "application/json;charset=UTF-8",
        #     "origin": "https://www.udemy.com",
        #     "referer": "https://www.udemy.com/",
        #     "dnt": "1",
        #     "User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)",
        # }

        headers = {
            "User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.5",
            "Referer": "https://www.udemy.com/",
            "X-Requested-With": "XMLHttpRequest",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        r = s.get(
            "https://www.udemy.com/api-2.0/contexts/me/?header=True",
            cookies=self.cookie_dict,
            headers=headers,
        )
        r = r.json()
        if r["header"]["isLoggedIn"] == False:
            raise LoginException("Login Failed")

        self.display_name: str = r["header"]["user"]["display_name"]
        r = s.get(
            "https://www.udemy.com/api-2.0/shopping-carts/me/",
            headers=headers,
            cookies=self.cookie_dict,
        )
        r = r.json()
        self.currency: str = r["user"]["credit"]["currency_code"]

        s = cloudscraper.CloudScraper()
        s.cookies.update(self.cookie_dict)
        s.headers.update(headers)
        s.keep_alive = False
        self.client = s

    def keyword_exclusion(self, title: str) -> bool:
        title_words = title.casefold().split()
        for word in title_words:
            word = word.casefold()
            if word in self.title_exclude:
                return True
        return False

    def is_user_dumb(self) -> bool:
        self.sites = [key for key, value in self.settings["sites"].items() if value]
        self.categories = [
            key for key, value in self.settings["categories"].items() if value
        ]
        self.languages = [
            key for key, value in self.settings["languages"].items() if value
        ]
        self.instructor_exclude = self.settings["instructor_exclude"]
        self.title_exclude = self.settings["title_exclude"]
        self.min_rating = self.settings["min_rating"]
        return not all([bool(self.sites), bool(self.categories), bool(self.languages)])

    def free_checkout(self, coupon: str, courseid: int):
        payload = {
            "checkout_environment": "Marketplace",
            "checkout_event": "Submit",
            "shopping_info": {
                "items": [
                    {
                        "discountInfo": {"code": coupon},
                        "buyable": {"type": "course", "id": courseid},
                        "price": {"amount": 0, "currency": self.currency.upper()},
                    }
                ]
            },
            "payment_info": {
                "method_id": "0",
                "payment_vendor": "Free",
                "payment_method": "free-method",
            },
        }

        # payload = json.dumps(payload)

        r = self.client.post(
            "https://www.udemy.com/payment/checkout-submit/",
            json=payload,
            verify=False,
        )
        try:
            r = r.json()
        except:
            return "retry"
        try:
            if r["status"] == "succeeded":
                return True
            elif r["status"] == "failed":
                return False
            else:
                print("404040404")
        except:
            return r["detail"]

    def free_subscribe(self, courseid: str):

        self.client.get(
            "https://www.udemy.com/course/subscribe/?courseId=" + courseid,
            verify=False,
        )

        r = self.client.get(
            "https://www.udemy.com/api-2.0/users/me/subscribed-courses/"
            + courseid
            + "/?fields%5Bcourse%5D=%40default%2Cbuyable_object_type%2Cprimary_subcategory%2Cis_private",
            verify=False,
        ).json()
        try:
            if r["_class"] == "course":
                return True

        except:
            return False

    def save_course(self, combo):  #### NOTE Pending
        if self.settings["save_txt"]:
            self.txt_file.write(combo + "\n")
            self.txt_file.flush()
            os.fsync(self.txt_file.fileno())

    def enrol(self):

        self.remove_duplicates()
        # main_window["pout"].update(0, max=len(self.scraped_links))
        (
            self.successfully_enrolled_c,
            self.already_enrolled_c,
            self.expired_c,
            self.excluded_c,
            self.amount_saved_c,
        ) = (0 for _ in range(5))

        if self.settings["save_txt"]:
            if not os.path.exists("Courses/"):
                os.makedirs("Courses/")
            self.txt_file = open(
                f"Courses/" + time.strftime("%Y-%m-%d--%H-%M") + ".txt",
                "w",
                encoding="utf-8",
            )

        index = 0
        total_courses = len(self.scraped_links)
        self.link = ""
        self.title = ""
        while index < total_courses:
            combo = self.scraped_links[index]
            self.title = combo.split("|:|")[0]
            self.link = combo.split("|:|")[1]
            self.print(
                f"[{str(index + 1)} / {str(total_courses)}] " + self.title,
                color="yellow",
                end=" ",
            )

            try:
                course_id, self.link = self.get_course_id(self.link)
                self.print(self.link, color="blue")
                if course_id == "retry":
                    self.print("Retrying..", color="red")
                    index += 1
                    continue

                if course_id:
                    coupon_id = self.extract_course_coupon(self.link)
                    purchased, amount, coupon_valid, coupon_id = self.check_course(
                        course_id, coupon_id
                    )

                    if not purchased:
                        if coupon_id and coupon_valid:
                            excluded = self.is_excluded(course_id, self.title)
                            if excluded == "0":
                                self.print("Retrying...\n", color="red")
                                index += 1
                                continue
                            elif not excluded:
                                success = self.free_checkout(coupon_id, course_id)
                                if success == "retry":
                                    self.print("Retrying....", color="red")
                                    index += 1
                                    continue
                                elif type(success) == str:
                                    self.print(f"{success}\n", color="light blue")
                                    slp = int(re.search(r"\d+", success).group(0))
                                    self.print(
                                        f">>> Pausing script for {slp} seconds\n",
                                        color="red",
                                    )
                                    time.sleep(slp)
                                    index += 1
                                    continue
                                elif success:
                                    self.print(
                                        "Successfully Enrolled To Course :)\n",
                                        color="green",
                                    )
                                    self.successfully_enrolled_c += 1
                                    self.amount_saved_c += amount
                                    self.save_course(combo)
                                elif not success:
                                    self.print("Coupon Expired :(\n", color="red")
                                    self.expired_c += 1
                                time.sleep(3)
                            else:
                                self.excluded_c += 1
                        elif coupon_id and not coupon_valid:
                            self.print(":( Coupon Expired\n", color="red")
                            self.expired_c += 1
                        elif not coupon_id:
                            if self.settings["discounted_only"]:
                                self.print("Free course excluded", color="light blue")
                                self.excluded_c += 1
                            else:
                                success = self.free_subscribe(course_id)
                                if success:
                                    self.print(
                                        "Successfully Subscribed\n",
                                        color="green",
                                    )
                                    self.successfully_enrolled_c += 1
                                    self.amount_saved_c += amount
                                    self.save_course(combo)
                                else:
                                    self.print("COUPON MIGHT HAVE EXPIRED", color="red")
                                    self.expired_c += 1

                    elif purchased == "retry":
                        self.print("Retrying.....\n", color="red")
                        index += 1
                        continue
                    elif purchased:
                        self.print(purchased + "\n", color="light blue")
                        self.already_enrolled_c += 1

                elif not course_id:
                    self.print("Course Expired", color="red")
                    self.expired_c += 1

            except Exception as e:
                self.print(f"Error processing course: {str(e)}\n", color="red")

            index += 1
