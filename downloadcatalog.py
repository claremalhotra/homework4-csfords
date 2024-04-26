#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 12:14:13 2024

@author: claremalhotra
"""

from io import StringIO
from time import sleep
import warnings
import bs4
import pandas as pd
import requests
from bs4 import MarkupResemblesLocatorWarning
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning, module = "bs4")


# discipline_list = ["artscore","biologicalsciencescore","civilizatio"]

def df_creator(course_page):
    """
    Given a page from the course catalog, this function return a pandas 
    dataframe containing the ontents of the responsive table
    """

    class_df = pd.DataFrame(columns = ["Course Code", "Course Name",
                                       "Description", "Professor",
                                       "Pre-Requisites", "Terms offered",
                                       "Equivalent Courses"])

    course_blocks = course_page.find_all("div",
                                        class_=["courseblock main",
                                                "courseblock subsequence"])

    for course_block in course_blocks:
        code_tag = course_block.find("p", class_="courseblocktitle").strong
        if code_tag:
            code = course_block.find("p", class_="courseblocktitle").\
                strong.text.split(".")[0]
            name = course_block.find("p", class_="courseblocktitle").\
                strong.text.split(".")[1:-2]
            name = "".join(name)
            description = course_block.find("p",
                                            class_ = "courseblockdesc").text
            description = description.replace("\n","")

            detail_tag = course_block.find("p", class_="courseblockdetail")
            if detail_tag:
                instructor_tag = course_block.find("p", class_=
                    "courseblockdetail").find(string=lambda text: text and
                    "Instructor(s)" in text)
                prerequisites_tag = course_block.find("p", class_=
                    "courseblockdetail").find(string=lambda text:
                    text and "Prerequisite(s):" in text)
                terms_tag = course_block.find("p", class_=
                    "courseblockdetail").find(string=lambda text:
                    text and "Terms Offered:" in text)
                equivalent_tag = course_block.find("p",
                    class_="courseblockdetail").find(string=lambda
                    text: text and "Equivalent Course(s):" in text)
                prof = ""
                prereqs = ""
                terms = ""
                equivs = ""

                if instructor_tag:
                    prof = instructor_tag.split("Instructor(s):")[1].strip()

                if terms_tag:
                    terms = terms_tag.split("Terms Offered:")[1].strip()
                    prof = prof.strip().split("Terms Offered")[0].strip()

                if prerequisites_tag:
                    prereqs = prerequisites_tag.split("Prerequisite(s):")\
                        [1].strip()
                    prof = prof.split("Prerequisite")[0].strip()
                    terms = terms.split("Prerequisite")[0].strip()

                if equivalent_tag:
                    equivs = equivalent_tag.split("Equivalent Course(s):")\
                        [1].strip()
                    prof = prof.split("Equivalent")[0].strip()
                    terms = terms.split("Equivalent")[0].strip()
                    prereqs = prereqs.split("Equivalent")[0].strip()

                df_dict = {"Course Code": code, "Course Name": name,
                           "Description": description, "Professor": prof,
                           "Pre-Requisites": prereqs, "Terms offered": terms,
                           "Equivalent Courses": equivs}

                df_dict = pd.DataFrame([df_dict])
                class_df = pd.concat([class_df, df_dict], ignore_index=True)

    return class_df

BASEURL = "http://collegecatalog.uchicago.edu/"

def url_finder(url, start_link, end_link):
    """
    This function returns the urls embedded in a page given a base url
    """
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.text, "html.parser")
    ul_element = soup.find("ul", class_="nav levelone")
    pagelinks = ul_element.find_all("a")
    link_stems = []
    for link in pagelinks[start_link:end_link]:
        link_stems.append(link["href"][1:]) #remove starting slash
    full_links = []
    for link in link_stems:
        full_link = BASEURL + link
        full_links.append(full_link)
    return full_links

stem_urls = url_finder(BASEURL, 0, 3)

core_page = stem_urls[0]
core_urls = url_finder(core_page,3,11)

major_page = stem_urls[1]
major_urls = url_finder(major_page, 2, 71)

def find_minor_urls(url, start_link = 0, end_link = -2):
    """
    This function returns the urls of minors, given the 
    url to the page from which all minors are linked
    """
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.text, "html.parser")
    minor_tag = soup.find("a", attrs = {"name": "minorsoffered"})
    minor_urls_list = []
    p_tags = minor_tag.find_all_next("p")
    for p_tag in p_tags:
        a_tags = p_tag.find_all("a")
        for a_tag in a_tags:
            minor_url = a_tag["href"][1:]
            minor_url = minor_url.replace("#","")
            minor_urls_list.append(minor_url)
    full_links = []
    for link in minor_urls[start_link:end_link]:
        full_link = BASEURL + link
        full_links.append(full_link)
    return full_links

minor_page = stem_urls[2]
minor_urls = find_minor_urls(minor_page, start_link = 0, end_link = -2)

all_urls = core_urls + major_urls + minor_urls

url_already_parsed = []
class_df = pd.DataFrame(columns = ["Course Code", "Course Name", "Description",
               "Professor","Pre-Requisites", "Terms offered", 
               "Equivalent Courses"])

def get_all_data(class_df):
    """
    This function parses through the list of urls, waiting three seconds
    between queries, and appending the data to a data frame
    """
    for url in all_urls:
        print(url)
        for item in url_already_parsed:
            if url == item:
                continue
        for i in range(6):
            try:
                page = requests.get(url)
                break
            except:
                print("got error")
                sleep(3)
                print(url)
                page = requests.get(url)
        page_text = page.text
        data = bs4.BeautifulSoup(StringIO(page_text), "html.parser")
        ind_df = df_creator(data)
        if len(ind_df) == 0:
            continue
        class_df = pd.concat([class_df, ind_df], ignore_index=True)
        url_already_parsed.append(url)
        sleep(3)
    return class_df

course_df = get_all_data(class_df)
course_df2 = course_df.drop_duplicates(subset = ["Course Code"])

# <codecell>

def unique_courses(course_df):
    """"
    This funcition returns the unique courses, removing 
    the cross-lised ones
    """
    for i in range(len(course_df)):
        mylist = [course_df.iloc[i]["Course Code"]]
        if not pd.isna(course_df.iloc[i]["Equivalent Courses"]):
            equivs = course_df.loc[i]["Equivalent Courses"].split(",")
            mylist = mylist + equivs
            mylist = [x.strip() for x in mylist]
            mylist.sort()
            course_df.at[i, "Course Code"] = mylist[0]
            course_df.at[i, "Equivalent Courses"] = ", ".join(mylist[1:])
    unique_df = course_df.drop_duplicates(subset = ["Course Code"])
    unique_df = unique_df.reset_index()
    unique_df = unique_df.drop(columns = {"Unnamed: 0", "index"})
    return unique_df

big_trial_df = pd.read_csv("/Users/claremalhotra/Desktop/cs_for_ds/trial7.csv")
unique_courses_df = unique_courses(big_trial_df)

def department_count(course_df):
    """
    This function returns a data frame with the count 
    of number of courses for each department
    """
    course_list = course_df["Course Code"].tolist()
    unique_courses = list(set(course_list))
    departments = list(set([x[0:4] for x in unique_courses]))

    dep_dict = {}
    for dep in departments:
        dep_count = 0
        for course_id in unique_courses:
            if dep in course_id:
                dep_count += 1
        dep_dict[dep] = dep_count

    dep_df = pd.DataFrame(list(dep_dict.items()), columns=['Department',
                                                           'Count'])
    return dep_df

dep_count_df = department_count(unique_courses_df)

def quarters_count(course_df):
    """
    This function determines the number of courses offered each quarter
    """
    quarter_dict = {}
    quarters = ["Autumn", "Winter", "Spring", "Summer"]
    for quarter in quarters:
        q_count = 0
        for course_qs in course_df["Terms offered"]:
            if not pd.isna(course_qs) and quarter in course_qs:
                q_count += 1
        quarter_dict[quarter] = q_count
    return quarter_dict
