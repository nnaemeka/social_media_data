import time
from bs4 import BeautifulSoup
import pandas as pd
import requests
import numpy as np
import datetime
import pickle
import os.path
import csv
import re

import psycopg2
import sys, os
import pandas.io.sql as psql 
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT # <-- ADD THIS LINE

def create_database():
    conn_string = "host='localhost' dbname='postgres' user='postgres' password='emeka'"
    con = psycopg2.connect(conn_string)
    con.autocommit = True

    cur = con.cursor()
    try:
        cur.execute('CREATE DATABASE social_media_data1')
        con.close()
    except:
        print('Database already exist .... moving ahead')
        con.close()
    return(0)  
    
def get_connection():
    #Define our connection string
    conn_string = "host='localhost' dbname='social_media_data1' user='postgres' password='emeka'"
 
    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
   
    return(conn)
 
def create_table():
    con = None
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS lib_blog(Id SERIAL PRIMARY KEY,\
                    Title VARCHAR,\
                    Username VARCHAR,\
                    Post VARCHAR,\
                    Time timestamp,\
                    Post_ID VARCHAR,\
                    Likes INTEGER,\
                    Dislikes INTEGER,\
                    Link VARCHAR)")
    
        con.commit()
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
            print('Error',e)   
        #sys.exit(1)
    finally:   
        if con:
            con.close()
    return(0)

def populate_table(article_stats):
    con = get_connection()
    cur = con.cursor()
    for i in article_stats:
        cur.execute("INSERT INTO lib_blog(Title,Username,Post,Time,Post_ID,Likes,Dislikes,Link) VALUES(%s, %s, %s,%s, %s, %s,%s,%s)",\
                    (str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4]),int(i[5]),int(i[6]),str(i[7])))
    con.commit()
    con.close()
    
def get_website(url):
    success = False
    try_counts = 0
    #print(url)
    while(success == False and try_counts<2): #two tries
        try:
            req = requests.get(url)
            success = True
            return(req)
        except:
            #print("Errors are encountered")
            #print("Will sleep for a 10 seconds")
            #pause = str(input("press 'y' to continue"))
            #try_counts +=1
            #time.sleep(10)
            return(None)
    return(0)
'''
def get_the_article(soup):
    # gets the article
    article = []
    link = soup.find('summary').find_all('p')
    for a in link:
        #text = 
        if a.text.strip() and a.text.strip()!= "(adsbygoogle = window.adsbygoogle || []).push({});"  :
            article.append(re.sub("\xa0", " ",a.get_text().strip()))
        #print(a.text.strip())
    post_time_stamp = soup.find('div',{'class':'post_age'}).text.split("at")[1]
    article_time = pd.to_datetime(post_time_stamp,format=" %d/%m/%Y %I:%M %p")
    return(" ".join(article),article_time) # join the list elements to a string

'''

def get_the_article(soup):
    # gets the article
    #article = []
    link = soup.find_all('summary')
    for a in link:
        #print(a) 
        if a.get_text().strip():
            #article = re.sub("\n", " ",a.get_text().strip())
            article = re.sub("\xa0", " ",a.get_text().strip())
            article = article.replace("?", "\'")
            if "(adsbygoogle = window.adsbygoogle || []).push({});" in article:
                article = article.split('\n')
    post_time_stamp = soup.find('div',{'class':'post_age'}).text.split("at")[1]
    #check if the date format is the standard given below. If not, return null objects
    try:
        article_time = pd.to_datetime(post_time_stamp,format=" %d/%m/%Y %I:%M %p")
    except:
        return(None,None)
    return(" ".join(article[1:]),article_time) # join the list elements to a string

def get_the_commenters_and_time(soup):
    #Gets the commenters and their time of commenting
    commenters = []
    for link in soup.find_all('div',{'class':'comment_top'}):
        comment_stat = link.get_text().strip()
        #print(user)
        commenters.append(comment_stat)
    user = []
    _time = [] 
    time_unit = []
    for entry in commenters:
        _user = entry.split(" about ")[0]
        t = entry.split(" about ")[-1].split()[0]
        #print(entry.split("about"))
        _time_unit = entry.split(" about ")[-1].split()[1]
        user.append(re.sub("\xa0", " ",_user))
        _time.append(t)
        time_unit.append(_time_unit)
    #print(time_unit)
    
    return(user,_time,time_unit)

def get_date_time(article_time,time_,time_unit):
    date = []
    for i,j in zip(time_,time_unit):
        if time_unit == "minutes":
            date.append(article_time + pd.DateOffset(minutes=time_))
        elif time_unit == "hours":
            date.append(article_time + pd.DateOffset(hours=time_))
        elif time_unit == "days":
            date.append(article_time + pd.DateOffset(days=time_))
        elif time_unit == "months":
            date.append(article_time + pd.DateOffset(months=time_))
        elif time_unit == "months":
            date.append(article_time + pd.DateOffset(years=time_))
        else:
            date.append(article_time)
    return(date)
        
def get_the_comments(soup):
    comments = []
    for link in soup.find_all('p',{"style":"font-size: 16px; margin-top: 6px;"}):
        #print(link.text)
        comment = link.get_text(strip=True)
        comments.append(re.sub("\n", "",comment)) # regex removes stuborn newlines "\n"
    return(comments)

def get_comment_likes_and_dislikes(soup):
    # gets comment likes and dislikes  
    likes_and_dislikes = []
    for element in soup.find_all(class_=True):
        counter = element["class"][0]
        if 'count_' in counter:
            likes_and_dislikes.append(element.text.strip())
    likes = likes_and_dislikes[0::2]
    dislikes = likes_and_dislikes[1::2]
    #print(likes,dislikes)
    return(likes,dislikes)

def get_starts_as_a_list(article,article_time,title,users,comments,time,comment_likes,comment_dislikes,link):
    number_of_comments = len(comments)
    post_stats = []
    post_stats.append([title,"Linda Ikeji",article,article_time,"article",-1,-1,link])
    for i,j,k,l,m in zip(users,comments,time,comment_likes,comment_dislikes):
        post_stats.append([title,i,j,k,"comment",l,m,link])
    return(post_stats)

def does_file_exist():
    headers = ["Title","Username","Post","Time","Post ID","Likes","Dislikes","Link"]
    if os.path.isfile("lib.csv"):
        pass
    else:
        _df = pd.DataFrame(columns = headers)
        _df.to_csv("lib.csv",index=False,sep='\\')
    return(0)

def save_processed_sites(sites):
    with open('visited_sites','wb') as f:
        pickle.dump(sites,f)
    return(0)

def load_processed_sites():
    try:
        with open ('visited_sites', 'rb') as f:
            sites = pickle.load(f)
    except:
        sites = []
    return(sites)