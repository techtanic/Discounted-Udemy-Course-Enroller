import json
import os
import re
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qs, unquote, urlparse, urlsplit, urlunparse

import cloudscraper
import requests
import rookiepy
from bs4 import BeautifulSoup as bs

from colors import *

VERSION = "v2.2"

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
    Scrapers: RD,TB, CV, IDC, EN, DU, UF
    """

    def __init__(
        self,
        site_to_scrape: list = list(scraper_dict.keys()),
        debug: bool = False,
    ):
        self.sites = site_to_scrape
        self.debug = debug
        for site in self.sites:
            code_name = scraper_dict[site]
            setattr(self, f"{code_name}_length", 0)
            setattr(self, f"{code_name}_data", [])
            setattr(self, f"{code_name}_done", False)
            setattr(self, f"{code_name}_progress", 0)
            setattr(self, f"{code_name}_error", "")

    def get_scraped_courses(self, target: object) -> list:
        threads = []
        scraped_data = {}
        for site in self.sites:
            t = threading.Thread(
                target=target,
                args=(site,),
                daemon=True,
            )
            t.start()
            threads.append(t)
            time.sleep(0.5)
        for t in threads:
            t.join()
        for site in self.sites:
            scraped_data[site] = getattr(self, f"{scraper_dict[site]}_data")
        return scraped_data

    def append_to_list(self, target: list, title: str, link: str):
        target.append((title, link))

    def fetch_page_content(self, url: str, headers: dict = None) -> bytes:
        return requests.get(url, headers=headers).content

    def parse_html(self, content: str):
        return bs(content, "html5lib")

    def handle_exception(self, site_code: str):
        setattr(self, f"{site_code}_error", traceback.format_exc())
        setattr(self, f"{site_code}_length", -1)
        setattr(self, f"{site_code}_done", True)
        if self.debug:
            print(getattr(self, f"{site_code}_error"))

    def cleanup_link(self, link: str) -> str:
        parsed_url = urlparse(link)

        if parsed_url.netloc == "www.udemy.com":
            return link

        if parsed_url.netloc == "click.linksynergy.com":
            query_params = parse_qs(parsed_url.query)

            if "RD_PARM1" in query_params:
                return unquote(query_params["RD_PARM1"][0])
            elif "murl" in query_params:
                return unquote(query_params["murl"][0])
            else:
                return ""
        raise ValueError(f"Unknown link format: {link}")

    def du(self):
        try:
            all_items = []
            head = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            }

            for page in range(1, 4):
                content = self.fetch_page_content(
                    f"https://www.discudemy.com/all/{page}", headers=head
                )
                soup = self.parse_html(content)
                page_items = soup.find_all("a", {"class": "card-header"})
                all_items.extend(page_items)
            self.du_length = len(all_items)
            if self.debug:
                print("Length:", self.du_length)
            for index, item in enumerate(all_items):
                self.du_progress = index
                title = item.string
                url = item["href"].split("/")[-1]
                content = self.fetch_page_content(
                    f"https://www.discudemy.com/go/{url}", headers=head
                )
                soup = self.parse_html(content)
                link = soup.find("div", {"class": "ui segment"}).a["href"]
                if self.debug:
                    print(title, link)
                self.append_to_list(self.du_data, title, link)

        except:
            self.handle_exception("du")
        self.du_done = True
        if self.debug:
            print("Return Length:", len(self.du_data))

    def uf(self):
        try:
            all_items = []
            for page in range(1, 4):
                content = self.fetch_page_content(
                    f"https://www.udemyfreebies.com/free-udemy-courses/{page}"
                )
                soup = self.parse_html(content)
                page_items = soup.find_all("a", {"class": "theme-img"})
                all_items.extend(page_items)
            self.uf_length = len(all_items)
            if self.debug:
                print("Length:", self.uf_length)
            for index, item in enumerate(all_items):
                title = item.img["alt"]
                link = requests.get(
                    f"https://www.udemyfreebies.com/out/{item['href'].split('/')[4]}"
                ).url
                self.append_to_list(self.uf_data, title, link)
                self.uf_progress = index

        except:
            self.handle_exception("uf")
        self.uf_done = True
        if self.debug:
            print("Return Length:", len(self.uf_data))

    def tb(self):
        try:
            all_items = []

            for page in range(1, 5):
                content = self.fetch_page_content(
                    f"https://www.tutorialbar.com/all-courses/page/{page}"
                )
                soup = self.parse_html(content)
                page_items = soup.find_all(
                    "h3", class_="mb15 mt0 font110 mobfont100 fontnormal lineheight20"
                )
                all_items.extend(page_items)
            self.tb_length = len(all_items)
            if self.debug:
                print("Length:", self.tb_length)

            for index, item in enumerate(all_items):
                self.tb_progress = index
                title = item.a.string
                url = item.a["href"]
                content = self.fetch_page_content(url)
                soup = self.parse_html(content)
                link = soup.find("a", class_="btn_offer_block re_track_btn")["href"]
                if "www.udemy.com" in link:
                    self.append_to_list(self.tb_data, title, link)

        except:
            self.handle_exception("tb")
        self.tb_done = True
        if self.debug:
            print("Return Length:", len(self.tb_data))

    def rd(self):
        all_items = []

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84",
                "Host": "www.real.discount",
                "Connection": "Keep-Alive",
                "dnt": "1",
            }
            try:
                r = requests.get(
                    "https://www.real.discount/api-web/all-courses/?store=Udemy&page=1&per_page=500&orderby=date&free=1&editorschoices=0",
                    headers=headers,
                    timeout=(10, 30),
                ).json()
            except requests.exceptions.Timeout:
                self.rd_error = "Timeout"
                self.rd_length = -1
                self.rd_done = True
                return
            all_items.extend(r["results"])

            self.rd_length = len(all_items)
            if self.debug:
                print("Length:", self.rd_length)
            for index, item in enumerate(all_items):
                self.rd_progress = index
                title: str = item["name"]
                link: str = item["url"]
                link = self.cleanup_link(link)
                if link:
                    self.append_to_list(self.rd_data, title, link)

        except:
            self.handle_exception("rd")
        if self.debug:
            print("Return Length:", len(self.rd_data))
        self.rd_done = True

    def cv(self):
        try:
            content = self.fetch_page_content("https://coursevania.com/courses/")
            soup = self.parse_html(content)
            try:
                nonce = json.loads(
                    re.search(
                        r"var stm_lms_nonces = ({.*?});", soup.text, re.DOTALL
                    ).group(1)
                )["load_content"]
                if self.debug:
                    print("Nonce:", nonce)
            except IndexError:
                self.cv_error = "Nonce not found"
                self.cv_length = -1
                self.cv_done = True
                return
            r = requests.get(
                "https://coursevania.com/wp-admin/admin-ajax.php?&template=courses/grid&args={%22posts_per_page%22:%2260%22}&action=stm_lms_load_content&nonce="
                + nonce
                + "&sort=date_high"
            ).json()

            soup = self.parse_html(r["content"])
            page_items = soup.find_all(
                "div", {"class": "stm_lms_courses__single--title"}
            )
            self.cv_length = len(page_items)
            if self.debug:
                print("Small Length:", self.cv_length)
            for index, item in enumerate(page_items):
                self.cv_progress = index
                title = item.h5.string
                content = self.fetch_page_content(item.a["href"])
                soup = self.parse_html(content)
                link = soup.find(
                    "a",
                    {"class": "masterstudy-button-affiliate__link"},
                )["href"]
                self.append_to_list(self.cv_data, title, link)

        except:
            self.handle_exception("cv")
        self.cv_done = True
        if self.debug:
            print("Return Length:", len(self.cv_data))

    def idc(self):
        try:
            all_items = []
            for page in range(1, 5):
                content = self.fetch_page_content(
                    f"https://idownloadcoupon.com/product-category/udemy/page/{page}"
                )
                soup = self.parse_html(content)
                page_items = soup.find_all(
                    "a",
                    attrs={
                        "class": "woocommerce-LoopProduct-link woocommerce-loop-product__link"
                    },
                )
                all_items.extend(page_items)
            self.idc_length = len(all_items)
            if self.debug:
                print("Length:", self.idc_length)
            for index, item in enumerate(all_items):
                self.idc_progress = index
                title = item.h2.string
                link_num = item["href"].split("/")[4]
                if link_num == "85":
                    continue
                link = f"https://idownloadcoupon.com/udemy/{link_num}/"

                r = requests.get(
                    link,
                    allow_redirects=False,
                )
                link = unquote(r.headers["Location"])
                link = self.cleanup_link(link)
                self.append_to_list(self.idc_data, title, link)

        except:
            self.handle_exception("idc")
        self.idc_done = True
        if self.debug:
            print("Return Length:", len(self.idc_data))

    def en(self):
        try:
            all_items = []
            for page in range(1, 6):
                content = self.fetch_page_content(
                    f"https://jobs.e-next.in/course/udemy/{page}"
                )
                soup = self.parse_html(content)
                page_items = soup.find_all(
                    "a", {"class": "btn btn-secondary btn-sm btn-block"}
                )
                all_items.extend(page_items)

            self.en_length = len(all_items)

            if self.debug:
                print("Length:", self.en_length)
            for index, item in enumerate(all_items):
                self.en_progress = index
                content = self.fetch_page_content(item["href"])
                soup = self.parse_html(content)
                title = soup.find("h3").string.strip()
                link = soup.find("a", {"class": "btn btn-primary"})["href"]
                self.append_to_list(self.en_data, title, link)

        except:
            self.handle_exception("en")
        self.en_done = True
        if self.debug:
            print("Return Length:", len(self.en_data))
            print(self.en_data)


class Udemy:
    def __init__(self, interface: str, debug: bool = False):
        self.interface = interface
        self.client = cloudscraper.CloudScraper()
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

        self.client.headers.update(headers)
        self.debug = debug

    def print(self, content: str, color: str, **kargs):
        colours_dict = {
            "yellow": fy,
            "red": fr,
            "blue": fb,
            "light blue": flb,
            "green": fg,
            "light green": flg,
            "cyan": fc,
            "magenta": fm,
        }
        if self.interface == "gui":
            self.window["out"].print(content, text_color=color, **kargs)
        else:
            print(colours_dict[color] + content, **kargs)

    def get_date_from_utc(self, d: str):
        utc_dt = datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")
        dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
        return dt.strftime("%B %d, %Y")

    def get_now_to_utc(self):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

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
        if (
            self.interface == "cli" and "use_browser_cookies" not in self.settings
        ):  # v2.1
            self.settings.get("use_browser_cookies", False)
        # v2.2
        if "course_update_threshold_months" not in self.settings:
            self.settings["course_update_threshold_months"] = 24  # 2 years

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
        cookies = rookiepy.to_cookiejar(rookiepy.load(["www.udemy.com"]))
        self.cookie_dict: dict = requests.utils.dict_from_cookiejar(cookies)
        self.cookie_jar = cookies

    def get_enrolled_courses(self):
        """Get enrolled courses
        Sets enrolled_courses {id:enrollment_time}
        """
        next_page = "https://www.udemy.com/api-2.0/users/me/subscribed-courses/?ordering=-enroll_time&fields[course]=enrollment_time&page_size=100"
        courses = {}
        while next_page:
            r = self.client.get(
                next_page,
            ).json()
            for course in r["results"]:
                courses[str(course["id"])] = course["enrollment_time"]
            next_page = r["next"]
        self.enrolled_courses = courses

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
        """Manual Login to Udemy using email and password and sets cookies
        Args:
            email (str): Email
            password (str): Password
        Raises:
            LoginException: Login Error
        """
        # s = cloudscraper.CloudScraper()

        s = requests.session()
        r = s.get(
            "https://www.udemy.com/join/signup-popup/",
            headers={"User-Agent": "okhttp/4.9.2 UdemyAndroid 8.9.2(499) (phone)"},
            # headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            #     'Accept-Language': 'en-US,en;q=0.5',
            #     #'Accept-Encoding': 'gzip, deflate, br',
            #     'DNT': '1',
            #     'Connection': 'keep-alive',
            #     'Upgrade-Insecure-Requests': '1',
            #     'Sec-Fetch-Dest': 'document',
            #     'Sec-Fetch-Mode': 'navigate',
            #     'Sec-Fetch-Site': 'none',
            #     'Sec-Fetch-User': '?1',
            #     'Pragma': 'no-cache',
            #     'Cache-Control': 'no-cache'},
        )
        try:
            csrf_token = r.cookies["csrftoken"]
        except:
            if self.debug:
                print(r.text)
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
        if self.debug:
            print(r)
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
        self.get_enrolled_courses()

    def is_keyword_excluded(self, title: str) -> bool:
        title_words = title.casefold().split()
        for word in title_words:
            word = word.casefold()
            if word in self.title_exclude:
                return True
        return False

    def is_instructor_excluded(self, instructors: list) -> bool:
        for instructor in instructors:
            if instructor in self.settings["instructor_exclude"]:
                return True
        return False

    def is_course_updated(self, last_update: str | None) -> bool:
        if not last_update:
            return True
        current_date = datetime.now()
        last_update_date = datetime.strptime(last_update, "%Y-%m-%d")
        # Calculate the difference in years and months
        years = current_date.year - last_update_date.year
        months = current_date.month - last_update_date.month
        days = current_date.day - last_update_date.day

        # Adjust the months and years if necessary
        if days < 0:
            months -= 1

        if months < 0:
            years -= 1
            months += 12

        # Calculate the total month difference
        month_diff = years * 12 + months
        return month_diff < self.settings["course_update_threshold_months"]

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

    def save_course(self):
        if self.settings["save_txt"]:
            self.txt_file.write(f"{self.title} - {self.link}\n")
            self.txt_file.flush()
            os.fsync(self.txt_file.fileno())

    def remove_duplicate_courses(self):
        existing_links = set()
        new_data = {}
        for key, courses in self.scraped_data.items():
            new_data[key] = []
            for title, link in courses:
                link = self.normalize_link(link)
                if link not in existing_links:
                    new_data[key].append((title, link))
                    existing_links.add(link)
        self.scraped_data = {k: v for k, v in new_data.items() if v}

    def normalize_link(self, link):
        parsed_url = urlparse(link)
        path = (
            parsed_url.path if parsed_url.path.endswith("/") else parsed_url.path + "/"
        )
        return urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                path,
                parsed_url.params,
                parsed_url.query,
                parsed_url.fragment,
            )
        )

    def get_course_id(self, url):
        url = re.sub(r"\W+$", "", unquote(url))
        try:
            r = self.client.get(url)
        except requests.exceptions.ConnectionError:
            if self.debug:
                print(r.text)
            return "retry", url, False

        soup = bs(r.content, "html5lib")
        if self.debug:
            with open("test/soup.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
        course_id = soup.find("body").get("data-clp-course-id", "invalid")
        if course_id == "invalid":
            return "invalid", url, False

        dma = json.loads(soup.find("body")["data-module-args"])
        if self.debug:
            with open("test/dma.json", "w") as f:
                json.dump(dma, f, indent=4)

        is_free = not dma["serverSideProps"]["course"].get("isPaid", True)
        if not self.debug and self.is_course_excluded(dma):
            return "excluded", r.url, False

        return course_id, r.url, is_free

    def is_course_excluded(self, dma):
        instructors = [
            i["absolute_url"].split("/")[-2]
            for i in dma["serverSideProps"]["course"]["instructors"]["instructors_info"]
            if i["absolute_url"]
        ]
        lang = dma["serverSideProps"]["course"]["localeSimpleEnglishTitle"]
        cat = dma["serverSideProps"]["topicMenu"]["breadcrumbs"][0]["title"]
        rating = dma["serverSideProps"]["course"]["rating"]
        last_update = dma["serverSideProps"]["course"]["lastUpdateDate"]

        if not self.is_course_updated(last_update):
            self.print(
                f"Course excluded: Last updated {last_update}", color="light blue"
            )
        elif self.is_instructor_excluded(instructors):
            self.print(f"Instructor excluded: {instructors[0]}", color="light blue")
        elif self.is_keyword_excluded(self.title):
            self.print("Keyword Excluded", color="light blue")
        elif cat not in self.categories:
            self.print(f"Category excluded: {cat}", color="light blue")
        elif lang not in self.languages:
            self.print(f"Language excluded: {lang}", color="light blue")
        elif rating < self.min_rating:
            self.print(f"Low rating: {rating}", color="light blue")
        else:
            return False
        return True

    def extract_course_coupon(self, url):
        params = parse_qs(urlsplit(url).query)
        return params.get("couponCode", [False])[0]

    def check_course(self, course_id, coupon_code=None):
        url = f"https://www.udemy.com/api-2.0/course-landing-components/{course_id}/me/?components=purchase"
        if coupon_code:
            url += f",redeem_coupon&couponCode={coupon_code}"

        r = self.client.get(url).json()
        if self.debug:
            with open("test/check_course.json", "w") as f:
                json.dump(r, f, indent=4)
        amount = (
            r.get("purchase", {})
            .get("data", {})
            .get("list_price", {})
            .get("amount", "retry")
        )
        coupon_valid = False

        if coupon_code and "redeem_coupon" in r:
            discount = r["purchase"]["data"]["pricing_result"]["discount_percent"]
            status = r["redeem_coupon"]["discount_attempts"][0]["status"]
            coupon_valid = discount == 100 and status == "applied"

        return Decimal(amount), coupon_valid

    def start_enrolling(self):
        self.remove_duplicate_courses()
        self.initialize_counters()
        self.setup_txt_file()

        total_courses = sum(len(courses) for courses in self.scraped_data.values())
        previous_courses_count = 0
        for site_index, (site, courses) in enumerate(self.scraped_data.items()):
            self.print(f"\nSite: {site} [{len(courses)}]", color="cyan")

            for index, (title, link) in enumerate(courses):
                self.title = title
                self.link = link
                self.print_course_info(previous_courses_count + index, total_courses)
                self.handle_course_enrollment(index)
            previous_courses_count += len(courses)

    def initialize_counters(self):
        self.successfully_enrolled_c = 0
        self.already_enrolled_c = 0
        self.expired_c = 0
        self.excluded_c = 0
        self.amount_saved_c = 0

    def setup_txt_file(self):
        if self.settings["save_txt"]:
            os.makedirs("Courses/", exist_ok=True)
            self.txt_file = open(
                f"Courses/{time.strftime('%Y-%m-%d--%H-%M')}.txt", "w", encoding="utf-8"
            )

    def print_course_info(self, index, total_courses):
        self.print(f"[{index + 1} / {total_courses}] ", color="magenta", end=" ")
        self.print(self.title, color="yellow", end=" ")
        self.print(self.link, color="blue")

    def handle_course_enrollment(self, index):
        course_id, self.link, is_free = self.get_course_id(self.link)

        if course_id == "invalid":
            self.print("Invalid Course", color="red")
            self.excluded_c += 1
        elif course_id == "excluded":
            self.excluded_c += 1
        elif not course_id:
            self.print("X Course Expired", color="red")
            self.expired_c += 1
        elif course_id in self.enrolled_courses:
            self.print(
                f"You purchased this course on {self.get_date_from_utc(self.enrolled_courses[course_id])}",
                color="light blue",
            )
            self.already_enrolled_c += 1
        elif is_free:
            self.handle_free_course(course_id)
        else:
            self.handle_discounted_course(course_id)

    def handle_free_course(self, course_id):
        if self.settings["discounted_only"]:
            self.print("Free course excluded", color="light blue")
            self.excluded_c += 1
        else:
            success = self.free_checkout(course_id)
            if success:
                self.print("Successfully Subscribed", color="green")
                self.successfully_enrolled_c += 1
                self.save_course()
            else:
                self.print(
                    "Unknown Error: Report this link to the developer", color="red"
                )
                self.expired_c += 1

    def discounted_checkout(self, coupon, course_id) -> dict:
        payload = {
            "checkout_environment": "Marketplace",
            "checkout_event": "Submit",
            "payment_info": {
                "method_id": "0",
                "payment_method": "free-method",
                "payment_vendor": "Free",
            },
            "shopping_info": {
                "items": [
                    {
                        "buyable": {"id": course_id, "type": "course"},
                        "discountInfo": {"code": coupon},
                        "price": {"amount": 0, "currency": self.currency.upper()},
                    }
                ]
            },
        }

        r: dict = self.client.post(
            "https://www.udemy.com/payment/checkout-submit/", json=payload
        ).json()
        if self.debug:
            print(r)

        return {"status": r.get("status") == "succeeded", "detail": r.get("detail")}

    def free_checkout(self, course_id):
        self.client.get(f"https://www.udemy.com/course/subscribe/?courseId={course_id}")
        r = self.client.get(
            f"https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/?fields%5Bcourse%5D=%40default%2Cbuyable_object_type%2Cprimary_subcategory%2Cis_private"
        ).json()
        return r.get("_class") == "course"

    def handle_discounted_course(self, course_id):
        coupon_code = self.extract_course_coupon(self.link)
        amount, coupon_valid = self.check_course(course_id, coupon_code)
        if amount == "retry":
            self.print("Retrying...", color="red")
            time.sleep(1)
            self.handle_discounted_course(course_id)
        elif coupon_valid:  # elif coupon_code and coupon_valid:
            self.process_coupon(course_id, coupon_code, amount)
        else:
            self.print("Coupon Expired", color="red")
            self.expired_c += 1

    def process_coupon(self, course_id, coupon_code, amount):
        checkout_response = self.discounted_checkout(coupon_code, course_id)
        if checkout_response["status"]:
            self.print("Successfully Enrolled To Course :)", color="green")
            self.successfully_enrolled_c += 1
            self.enrolled_courses[course_id] = self.get_now_to_utc()
            self.amount_saved_c += amount
            self.save_course()
            time.sleep(3.6)
        else:
            self.print(checkout_response["detail"], color="light blue")
            wait_time = int(re.search(r"\d+", checkout_response["detail"]).group(0))
            self.print(f">>> Pausing script for {wait_time} seconds\n", color="red")
            time.sleep(wait_time + 1)
            self.process_coupon(course_id, coupon_code, amount)
