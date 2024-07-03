import threading
import time
import traceback

from tqdm import tqdm

from base import VERSION, LoginException, Scraper, Udemy, scraper_dict
from colors import *

# DUCE-CLI


def create_scraping_thread(site: str):

    code_name = scraper_dict[site]
    try:
        t = threading.Thread(target=getattr(scraper, code_name), daemon=True)
        t.start()
        while getattr(scraper, f"{code_name}_length") == 0:
            time.sleep(0.1)  # Avoid busy waiting
        if getattr(scraper, f"{code_name}_length") == -1:
            raise Exception(f"Error in: {site}")
        progress_bar = tqdm(
            total=getattr(scraper, f"{code_name}_length"), desc=site, leave=False
        )
        prev_progress = -1

        while prev_progress != getattr(scraper, f"{code_name}_length"):
            time.sleep(0.1)
            progress_bar.update(
                getattr(scraper, f"{code_name}_progress") - prev_progress
            )
            prev_progress = getattr(scraper, f"{code_name}_progress")
            if getattr(scraper, f"{code_name}_done"):
                break
        # progress_bar.close()
    except Exception as e:
        error = getattr(scraper, f"{code_name}_error", traceback.format_exc())
        print(error)
        print("\nError in: " + site + " " + str(VERSION))


##########################################

udemy = Udemy("cli")
udemy.load_settings()
login_title, main_title = udemy.check_for_update()
if login_title.__contains__("Update"):
    print(by + fr + login_title)

############## MAIN #############

login_error = True
while login_error:
    try:
        if udemy.settings["use_browser_cookies"]:
            udemy.fetch_cookies()
            using = "Browser Cookies"
        elif udemy.settings["email"] and udemy.settings["password"]:
            email, password = udemy.settings["email"], udemy.settings["password"]
            using = "Saved Email and Password"
        else:
            email = input("Email: ")
            password = input("Password: ")
            using = "Email and Password"
        print(fb + f"Trying to login using {using}")
        if "Email" in using:
            udemy.manual_login(email, password)
        udemy.get_session_info()
        if "Email" in using:
            udemy.settings["email"], udemy.settings["password"] = email, password
        login_error = False
    except LoginException as e:
        print(fr + str(e))
        if "Browser" in using:
            print("Make sure you have logged in to Udemy in your browser")
        elif "Email" in using:
            udemy.settings["email"], udemy.settings["password"] = "", ""

    udemy.save_settings()

print(fg + f"Logged in as {udemy.display_name}")
user_dumb = udemy.is_user_dumb()
if user_dumb:
    print(bw + fr + "What do you even expect to happen!")
    exit()
if not user_dumb:
    scraper = Scraper(udemy.sites)
try:
    udemy.scraped_data = scraper.get_scraped_courses(create_scraping_thread)
    time.sleep(0.5)
    print("\n")
    udemy.start_enrolling()

    udemy.print(
        f"\nSuccessfully Enrolled: {udemy.successfully_enrolled_c}", color="green"
    )
    udemy.print(
        f"Amount Saved: {round(udemy.amount_saved_c,2)} {udemy.currency.upper()}",
        color="light green",
    )
    udemy.print(f"Already Enrolled: {udemy.already_enrolled_c}", color="blue")
    udemy.print(f"Excluded Courses: {udemy.excluded_c}", color="yellow")
    udemy.print(f"Expired Courses: {udemy.expired_c}", color="red")

except:
    e = traceback.format_exc()
    print(
        (
            "Error",
            e + f"\n\n{udemy.link}\n{udemy.title}" + f"|:|Unknown Error {VERSION}",
        )
    )
input("Press Enter to exit...")
