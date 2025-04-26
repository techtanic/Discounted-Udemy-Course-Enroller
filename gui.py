import os
import sys
import threading
import time
import traceback
from webbrowser import open as web

import FreeSimpleGUI as sg

from base import LINKS, VERSION, LoginException, Scraper, Udemy, scraper_dict, logger
from images import (
    auto_login,
    back,
    check_mark,
    exit_,
    icon,
    login,
    logout,
    manual_login_,
    start,
)

sg.set_global_icon(icon)

sg.change_look_and_feel("dark")
sg.theme_background_color
sg.set_options(
    button_color=(sg.theme_background_color(), sg.theme_background_color()),
    border_width=0,
    font=10,
)


def update_enrolled_courses():
    while True:
        logger.debug(f"Enrolled courses count: {len(udemy.enrolled_courses)}")
        new_menu = [
            ["Help", ["Support", "Github", "Discord"]],
            [f"Total Courses: {len(udemy.enrolled_courses)}"],
        ]
        main_window.write_event_value("Update-Menu", new_menu)
        time.sleep(10)


def create_scraping_thread(site: str):
    logger.info(f"Launching scraping thread for site: {site}")
    code_name = scraper_dict[site]
    main_window[f"i{site}"].update(visible=False)
    main_window[f"p{site}"].update(0, visible=True)

    try:
        threading.Thread(target=getattr(scraper, code_name), daemon=True).start()
        while getattr(scraper, f"{code_name}_length") == 0:
            time.sleep(0.1)
        if getattr(scraper, f"{code_name}_length") == -1:

            raise Exception(f"Error in: {site}")
        main_window[f"p{site}"].update(0, max=getattr(scraper, f"{code_name}_length"))
        while not getattr(scraper, f"{code_name}_done") and not getattr(
            scraper, f"{code_name}_error"
        ):
            main_window[f"p{site}"].update(
                getattr(scraper, f"{code_name}_progress") + 1,
                max=getattr(scraper, f"{code_name}_length"),
            )

            time.sleep(0.1)
        logger.info(
            f"Courses Found {code_name}: {len(getattr(scraper, f'{code_name}_data'))}"
        )
        if getattr(scraper, f"{code_name}_error"):
            raise Exception(f"Error in: {site}")
    except Exception:
        error_message = getattr(scraper, f"{code_name}_error", "Unknown Error")
        logger.exception(f"Error in {site}: {error_message}")
        main_window.write_event_value(
            "Error", f"{error_message}|:|Unknown Error in: {site} {VERSION}"
        )
    finally:
        main_window[f"p{site}"].update(0, visible=False)
        main_window[f"i{site}"].update(visible=True)


##########################################


def scrape():
    try:
        for site in udemy.sites:
            main_window[f"pcol{site}"].update(visible=True)
        main_window["main_col"].update(visible=False)
        main_window["scrape_col"].update(visible=True)
        udemy.scraped_data = scraper.get_scraped_courses(create_scraping_thread)
        main_window["scrape_col"].update(visible=False)

        main_window["enrollment_panel"].update(visible=True)
        main_window["stats_panel"].update(visible=True)
        main_window["current_course_panel"].update(visible=True)

        total_courses = len(udemy.scraped_data)

        def update_progress():

            if hasattr(udemy, "course") and udemy.course:
                main_window["current_course_title"].update(value=udemy.course.title)
                main_window["current_course_url"].update(value=udemy.course.url)

            if hasattr(udemy, "total_courses_processed"):
                progress_text = (
                    f"Course {udemy.total_courses_processed:4d}/{total_courses:4d}"
                )
                main_window["course_progress"].update(value=progress_text)

            main_window["stat_enrolled"].update(
                value=f"{udemy.successfully_enrolled_c}"
            )
            main_window["stat_amount_saved"].update(
                value=f"{round(udemy.amount_saved_c, 2)} {udemy.currency.upper()}"
            )
            main_window["stat_already"].update(value=f"{udemy.already_enrolled_c}")
            main_window["stat_excluded"].update(value=f"{udemy.excluded_c}")
            main_window["stat_expired"].update(value=f"{udemy.expired_c}")

            ready_count = len(getattr(udemy, "valid_courses", []))
            main_window["stat_ready_enroll"].update(value=f"{ready_count}/5")

        udemy.update_progress = update_progress

        udemy.total_courses_processed = 0

        # Start enrollment process
        udemy.start_new_enroll()

        main_window["enrollment_panel"].update(visible=False)
        main_window["done_col"].update(visible=True)

        main_window["se_c"].update(
            value=f"Successfully Enrolled: {udemy.successfully_enrolled_c}"
        )
        main_window["as_c"].update(
            value=f"Amount Saved: {round(udemy.amount_saved_c,2)} {udemy.currency.upper()}"
        )
        main_window["ae_c"].update(
            value=f"Already Enrolled: {udemy.already_enrolled_c}"
        )
        main_window["e_c"].update(value=f"Expired Courses: {udemy.expired_c}")
        main_window["ex_c"].update(value=f"Excluded Courses: {udemy.excluded_c}")

    except Exception:
        e = traceback.format_exc()

        logger.exception(
            f"Error during scraping/enrollment: {e}\nCourse: {str(udemy.course)}"
        )

        main_window.write_event_value(
            "Error",
            e + f"\n\n{str(udemy.course)}" + f"|:|Error {VERSION}",
        )


#################################


udemy = Udemy("gui")
logger.info("Starting GUI application")
udemy.load_settings()
login_title, main_title = udemy.check_for_update()


menu = [["Help", ["Support", "Github", "Discord"]]]

login_error = False

try:
    if udemy.settings["stay_logged_in"]["auto"]:
        udemy.fetch_cookies()

    elif udemy.settings["stay_logged_in"]["manual"]:
        udemy.manual_login(udemy.settings["email"], udemy.settings["password"])
    else:
        raise LoginException("No Saved Login Found")
    udemy.get_session_info()
except LoginException:
    login_error = True
# if (
#     not udemy.settings["stay_logged_in"]["auto"]
#     and not udemy.settings["stay_logged_in"]["manual"]
# ) or login_error:
if login_error:
    c1 = [
        [
            sg.Button(key="a_login", image_data=auto_login),
            sg.T(""),
            sg.B(key="m_login", image_data=manual_login_),
        ],
        [
            sg.Checkbox(
                "Stay logged-in",
                default=udemy.settings["stay_logged_in"]["auto"],
                key="sli_a",
            )
        ],
    ]
    c2 = [
        [
            sg.T("Email"),
            sg.InputText(
                default_text=udemy.settings["email"],
                key="email",
                size=(20, 1),
                pad=(5, 5),
            ),
        ],
        [
            sg.T("Password"),
            sg.InputText(
                default_text=udemy.settings["password"],
                key="password",
                size=(20, 1),
                pad=(5, 5),
                password_char="*",
            ),
        ],
        [
            sg.Checkbox(
                "Stay logged-in",
                default=udemy.settings["stay_logged_in"]["manual"],
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

    login_window = sg.Window(login_title, login_layout, finalize=True)
    while True:
        event, values = login_window.read()
        logger.info(f"Login window event: {event}")
        if event in (None,):
            login_window.close()
            sys.exit()

        elif event == "a_login" and not login_window["a_login"].Disabled:
            login_window["a_login"].update(disabled=True)
            login_window.refresh()
            try:
                udemy.fetch_cookies()
                try:
                    udemy.get_session_info()
                    udemy.settings["stay_logged_in"]["auto"] = values["sli_a"]
                    udemy.save_settings()
                    login_window.close()
                    break
                except Exception:
                    logger.exception("Error in auto login")
                    sg.popup_auto_close(
                        "Make sure you are logged in to udemy.com in your browser",
                        title="Error",
                        auto_close_duration=3,
                        no_titlebar=True,
                    )

            except Exception:
                logger.exception("Error in auto login")
                e = traceback.format_exc()
                sg.popup_scrolled(e, title=f"Unknown Error {VERSION}")

            login_window["a_login"].update(disabled=False)
        elif event == "m_login":
            login_window["col1"].update(visible=False)
            login_window["col2"].update(visible=True)

            login_window["email"].update(value=udemy.settings["email"])
            login_window["password"].update(value=udemy.settings["password"])

        elif event == "Github":
            web(LINKS["github"])

        elif event == "Support":
            web(LINKS["support"])

        elif event == "Discord":
            web(LINKS["discord"])

        elif event == "Back":
            login_window["col1"].update(visible=True)
            login_window["col2"].update(visible=False)

        elif event == "Login":
            udemy.settings["email"] = values["email"]
            udemy.settings["password"] = values["password"]
            try:
                try:
                    udemy.manual_login(
                        udemy.settings["email"], udemy.settings["password"]
                    )
                    udemy.get_session_info()
                    udemy.settings["stay_logged_in"]["manual"] = values["sli_m"]
                    udemy.save_settings()
                    login_window.close()
                    break
                except LoginException as e:
                    sg.popup_auto_close(
                        e,
                        title="Error",
                        auto_close_duration=3,
                        no_titlebar=True,
                    )
            except Exception:
                e = traceback.format_exc()
                logger.exception()
                sg.popup_scrolled(e, title=f"Unknown Error {VERSION}")

checkbox_lo = []
for key in udemy.settings["sites"]:
    checkbox_lo.append(
        [sg.Checkbox(key, key=key, default=udemy.settings["sites"][key], size=(18, 1))]
    )

categories_lo = []
categories_k = list(udemy.settings["categories"].keys())
categories_v = list(udemy.settings["categories"].values())
for index, _ in enumerate(udemy.settings["categories"]):
    if index % 3 == 0:
        try:
            categories_lo.append(
                [
                    sg.Checkbox(
                        categories_k[index],
                        default=categories_v[index],
                        key=categories_k[index],
                        size=(18, 1),
                    ),
                    sg.Checkbox(
                        categories_k[index + 1],
                        default=categories_v[index + 1],
                        key=categories_k[index + 1],
                        size=(18, 1),
                    ),
                    sg.Checkbox(
                        categories_k[index + 2],
                        default=categories_v[index + 2],
                        key=categories_k[index + 2],
                        size=(18, 1),
                    ),
                ]
            )
        except IndexError:
            categories_lo.append(
                [
                    sg.Checkbox(
                        categories_k[index],
                        default=categories_v[index],
                        key=categories_k[index],
                        size=(18, 1),
                    )
                ]
            )

languages_lo = []
languages_k = list(udemy.settings["languages"].keys())
languages_v = list(udemy.settings["languages"].values())
for index, _ in enumerate(udemy.settings["languages"]):
    if index % 3 == 0:
        try:
            languages_lo.append(
                [
                    sg.Checkbox(
                        languages_k[index],
                        default=languages_v[index],
                        key=languages_k[index],
                        size=(10, 1),
                    ),
                    sg.Checkbox(
                        languages_k[index + 1],
                        default=languages_v[index + 1],
                        key=languages_k[index + 1],
                        size=(10, 1),
                    ),
                    sg.Checkbox(
                        languages_k[index + 2],
                        default=languages_v[index + 2],
                        key=languages_k[index + 2],
                        size=(10, 1),
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
                        size=(10, 1),
                    ),
                    sg.Checkbox(
                        languages_k[index + 1],
                        default=languages_v[index + 1],
                        key=languages_k[index + 1],
                        size=(10, 1),
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
            default_text=udemy.instructor_exclude,
            key="instructor_exclude",
            size=(15, 10),
        )
    ],
    [sg.Text("Paste instructor(s)\nusername in new lines")],
]
title_ex_lo = [
    [
        sg.Multiline(
            default_text=udemy.title_exclude, key="title_exclude", size=(20, 10)
        )
    ],
    [sg.Text("Keywords in new lines\nNot cAsE sensitive")],
]

rating_lo = [
    [
        sg.Spin(
            [i * 0.5 for i in range(11)],
            initial_value=udemy.settings["min_rating"],
            key="min_rating",
        ),
        sg.Text("0.0 <-> 5.0"),
    ]
]

courses_last_updated_lo = [
    [
        sg.Text("Past"),
        sg.Spin(
            [i for i in range(1, 48)],
            initial_value=udemy.settings["course_update_threshold_months"],
            key="course_update_threshold_months",
        ),
        sg.Text("Month(s)"),
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
        ),
        sg.Frame(
            "Title Keyword Exclusion",
            title_ex_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
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
        ),
        sg.Frame(
            "Course Last Updated",
            courses_last_updated_lo,
            "#4deeea",
            border_width=4,
            title_location="n",
            key="f_course_last_updated",
            font=25,
        ),
    ],
    [
        sg.Checkbox(
            "Save enrolled courses in txt",
            key="save_txt",
            default=udemy.settings["save_txt"],
        )
    ],
    [
        sg.Checkbox(
            "Enrol in Discounted courses only",
            key="discounted_only",
            default=udemy.settings["discounted_only"],
        )
    ],
]


scrape_col = []
for key in udemy.settings["sites"]:
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
    [sg.Multiline(size=(69, 12), key="out", autoscroll=False, disabled=True)],
    # [
    #     sg.ProgressBar(
    #         3,
    #         orientation="h",
    #         key="pout",
    #         bar_color=("#1c6fba", "#000000"),
    #         border_width=1,
    #         size=(46, 20),
    #     )
    # ],
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
            "Amount Saved:                                   ",
            key="as_c",
            text_color="#00FA9A",
        )
    ],
    [sg.Text("Already Enrolled:              ", key="ae_c", text_color="#00FFFF")],
    [sg.Text("Expired Courses:           ", key="e_c", text_color="#FF0000")],
    [sg.Text("Excluded Courses:          ", key="ex_c", text_color="#FF4500")],
]

current_course_panel = [
    [
        sg.Text(
            "Current Course",
            font=("Helvetica", 12, "bold"),
            key="course_progress",
            text_color="#FFD700",
        )
    ],
    [
        sg.Text("Title:", text_color="#4deeea"),
        sg.Text("", size=(60, 1), key="current_course_title", text_color="#FFFFFF"),
    ],
    [
        sg.Text("URL:", text_color="#4deeea"),
        sg.Multiline(
            "",
            size=(60, 2),
            key="current_course_url",
            text_color="#00BFFF",
            no_scrollbar=True,
            disabled=True,
            autoscroll=False,
            border_width=0,
        ),
    ],
]


stats_panel = [
    [sg.Text("Enrollment Stats", font=("Helvetica", 12, "bold"), text_color="#FFD700")],
    [
        sg.Text("Successfully Enrolled:", text_color="#4deeea", size=(18, 1)),
        sg.Text("0", key="stat_enrolled", text_color="#7CFC00", size=(8, 1)),
        sg.Text("Already Enrolled:", text_color="#4deeea", size=(15, 1)),
        sg.Text("0", key="stat_already", text_color="#00FFFF", size=(8, 1)),
        sg.Text("Expired Courses:", text_color="#4deeea", size=(15, 1)),
        sg.Text("0", key="stat_expired", text_color="#FF0000", size=(8, 1)),
    ],
    [
        sg.Text("Amount Saved:", text_color="#4deeea", size=(12, 1)),
        sg.Text(
            f"0 {udemy.currency.upper()}",
            key="stat_amount_saved",
            text_color="#00FA9A",
            size=(14, 1),
        ),
        sg.Text("Excluded Courses:", text_color="#4deeea", size=(15, 1)),
        sg.Text("0", key="stat_excluded", text_color="#FF4500", size=(8, 1)),
        sg.Text("Pending Enrollment:", text_color="#4deeea", size=(15, 1)),
        sg.Text("0/20", key="stat_ready_enroll", text_color="#FFA500", size=(8, 1)),
    ],
]


enrollment_panel = [
    [sg.Column(stats_panel, key="stats_panel", visible=False)],
    [sg.Column(current_course_panel, key="current_course_panel", visible=False)],
]

main_col = [
    [
        sg.TabGroup(
            [[sg.Tab("Main", main_tab), sg.Tab("Advanced", advanced_tab)]],
            border_width=2,
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

if (
    udemy.settings["stay_logged_in"]["auto"]
    or udemy.settings["stay_logged_in"]["manual"]
):
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
    [sg.Text(f"Logged in as: {udemy.display_name}", key="user_t"), logout_btn_lo],
    [
        sg.pin(sg.Column(main_col, key="main_col")),
        sg.pin(sg.Column(output_col, key="output_col", visible=False)),
        sg.pin(sg.Column(scrape_col, key="scrape_col", visible=False)),
        sg.pin(sg.Column(done_col, key="done_col", visible=False)),
        sg.pin(sg.Column(enrollment_panel, key="enrollment_panel", visible=False)),
    ],
    [
        sg.Button(key="Exit", image_data=exit_),
        sg.Text("Made with 🩷 by techtanic", justification="right", expand_x=True),
    ],
]


global main_window


main_window = sg.Window(
    main_title,
    main_lo,
    finalize=True,
)
threading.Thread(target=update_enrolled_courses, daemon=True).start()
while True:
    event, values = main_window.read()

    logger.info(f"Main window event: {event}")
    if event == "Dummy":
        logger.debug(f"Dummy event values: {values}")

    if event in (None, "Exit"):
        break

    elif event == "Logout":
        (
            udemy.settings["stay_logged_in"]["auto"],
            udemy.settings["stay_logged_in"]["manual"],
        ) = (
            False,
            False,
        )
        udemy.save_settings()
        break

    elif event == "Support":
        web(LINKS["support"])

    elif event == "Github":
        web(LINKS["github"])

    elif event == "Discord":
        web(LINKS["discord"])

    elif event == "Start" and main_window["main_col"].visible:

        for setting in ["languages", "categories", "sites"]:
            for key in udemy.settings[setting]:
                udemy.settings[setting][key] = values[key]

        udemy.settings["instructor_exclude"] = str(values["instructor_exclude"]).split()
        udemy.settings["title_exclude"] = list(
            filter(None, values["title_exclude"].split("\n"))
        )
        udemy.settings["min_rating"] = float(values["min_rating"])
        udemy.settings["course_update_threshold_months"] = int(
            values["course_update_threshold_months"]
        )
        udemy.settings["save_txt"] = values["save_txt"]
        udemy.settings["discounted_only"] = values["discounted_only"]
        udemy.save_settings()

        user_dumb = udemy.is_user_dumb()
        if user_dumb:
            sg.popup_auto_close(
                "What do you even expect to happen!",
                auto_close_duration=5,
                no_titlebar=True,
            )
            continue
        scraper = Scraper(udemy.sites)
        udemy.window = main_window
        threading.Thread(target=scrape, daemon=True).start()

    elif event == "Error":
        msg = values["Error"].split("|:|")
        error_text = msg[0]
        title = msg[1]

        logger.exception(f"GUI Error Popup: {title} - {error_text}")

        sg.popup_scrolled(error_text, title=title)
    elif event == "Update-Menu":
        menu = values["Update-Menu"]
        main_window["mn"].update(menu)
main_window.close()
