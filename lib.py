import time
import pandas as pd
import numpy as np
import os.path

import header

create_database()
create_table()
number_of_pages = int(input("How many pages do you want to proccess"))
position = 0
does_file_exist()
processed_sites = load_processed_sites()
headers = ["Title","Username","Post","Time","Post ID","Likes","Dislikes","Link"]
print("Number of proccessed posts are:", len(processed_sites))
for i in range(number_of_pages):
    print("processing page",i+1,"....")
    if i+1 == 1:
        website = "https://www.lindaikejisblog.com/"
    else:
        website = "https://www.lindaikejisblog.com/page/"+str(i+1)
    req = get_website(website)
    if req == None:
        continue
    soup = BeautifulSoup(req.text, 'html.parser')
    for a in soup.find_all('a', href=True):
    #print("Found the URL:", a['href'])
    #print(a['href'][:11],a['href'].split())
        url = a['href']
        begin = "https://www.lindaikejisblog.com/"
        if position >=17 and url != "javascript:;" and begin in url and url[-9:] == "#comments":
            if url in processed_sites:
                #print(url,"Already proccessed")
                pass
            else:
                #print(url)
                req = get_website(url)
                if req == None:
                    continue
                soup = BeautifulSoup(req.text, 'html.parser')
                title = soup.title.text
                #print(title)
                article,article_time = get_the_article(soup)
                users, _time, time_unit = get_the_commenters_and_time(soup)
                date_time = get_date_time(article_time,_time, time_unit)
                comments = get_the_comments(soup)
                comment_likes, comment_dislikes = get_comment_likes_and_dislikes(soup)
                article_stats = get_starts_as_a_list(article,article_time,title,users,comments,date_time,comment_likes,comment_dislikes,url)
                populate_table(article_stats)
                df3 = pd.DataFrame(article_stats, columns=headers)
                df3.to_csv("lib.csv",mode='a',header=False,index=False, encoding='utf-8', sep='\\',quoting=csv.QUOTE_NONNUMERIC)
                processed_sites.append(url)
                save_processed_sites(processed_sites)
        position+=1
    #time.sleep(5)
    #if i>581:
        #print(url)
        #time.sleep(5)
    #else:
        #pass
#df = pd.concat((d_f for d_f in article_stats),axis=0)
#df = pd.concat((pd.DataFrame(d_f, columns=headers) for d_f in article_stats),axis=0)
print("Done!!!")
