import traceback
import threading
import time
from tqdm import tqdm
from base import VERSION, LoginException, Scraper, Udemy, scraper_dict
from colors import *

def create_scraping_thread(site: str):
    code_name = scraper_dict[site]

    def scrape_site():
        try:
            getattr(scraper, code_name)()
        except Exception as e:
            error_message = getattr(scraper, f"{code_name}_error", "Unknown Error")
            print(error_message)
            print("\nUnknown Error in: " + site + " " + str(VERSION))

    thread = threading.Thread(target=scrape_site, daemon=True)
    thread.start()

    while getattr(scraper, f"{code_name}_length") == 0:
        pass
    if getattr(scraper, f"{code_name}_length") == -1:
        raise Exception("Error in: " + site)

    with tqdm(total=getattr(scraper, f"{code_name}_length"), desc=site) as pbar:
        prev_progress = 0
        while thread.is_alive():
            new_progress = getattr(scraper, f"{code_name}_progress")
            if new_progress > prev_progress:
                pbar.update(new_progress - prev_progress)
                prev_progress = new_progress
            time.sleep(0.5)
        # Ensure the progress bar completes if thread ends prematurely
        final_progress = getattr(scraper, f"{code_name}_progress")
        if final_progress > prev_progress:
            pbar.update(final_progress - prev_progress)
        pbar.close()

def scrape():
    try:
        udemy.scraped_links = scraper.get_scraped_courses(create_scraping_thread)
        print("\n")
        udemy.enrol()

        print(f"Successfully Enrolled: {udemy.successfully_enrolled_c}")
        print(f"Amount Saved: {round(udemy.amount_saved_c, 2)} {udemy.currency.upper()}")
        print(f"Already Enrolled: {udemy.already_enrolled_c}")
        print(f"Expired Courses: {udemy.expired_c}")
        print(f"Excluded Courses: {udemy.excluded_c}")

    except:
        e = traceback.format_exc()
        print("Error", e + f"\n\n{udemy.link}\n{udemy.title}" + f"|:|Unknown Error {VERSION}")

udemy = Udemy("cli")
udemy.load_settings()
login_title, main_title = udemy.check_for_update()
if login_title.__contains__("Update"):
    print(by + fr + login_title)

login_error = True
while login_error:
    try:
        if udemy.settings["email"] and udemy.settings["password"]:
            email, password = udemy.settings["email"], udemy.settings["password"]
        else:
            email = input("Email: ")
            password = input("Password: ")
        print(fb + "Trying to login")
        udemy.manual_login(email, password)
        udemy.get_session_info()
        udemy.settings["email"], password = email, password
        login_error = False
    except LoginException as e:
        print(fr + str(e))
        udemy.settings["email"], password = "", ""
    udemy.save_settings()

print(fg + f"Logged in as {udemy.display_name}")
user_dumb = udemy.is_user_dumb()
if user_dumb:
    print(bw + fr + "What do you even expect to happen!")
if not user_dumb:
    scraper = Scraper(udemy.sites)
    scrape()
input()
