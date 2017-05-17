# coding=utf-8

import re
from bs4 import BeautifulSoup
import requests
import MySQLdb

PAGE = input("PAGE: ")
TIME_MATCH = r'title=.*"'
AUTHOR_MATCH = r'title=.*"'
TITLE_MATCH = r'blank">.*<'
FLAG_MATCH = r'blank">.*<'


class Spider(object):
    def __init__(self):
        self.url = 'http://127.0.0.1:8080/activity/?db=' + str(PAGE)
        self.author_list = []
        self.time_list = []
        self.title_list = []
        self.flag_list = []

    def get_page(self):
        r = requests.get(self.url)
        r.encoding = 'UTF8'
        soup = BeautifulSoup(r.text)
        time_p = re.compile(TIME_MATCH)
        author_p = re.compile(AUTHOR_MATCH)
        title_p = re.compile(TITLE_MATCH)
        flag_p = re.compile(FLAG_MATCH)

        for tag in soup.find_all('div', style='padding-bottom:10px;'):
            for tag_author in tag.find_all('img', class_='gravatar'):
                author = author_p.search(str(tag_author))
                if author:
                    self.author_list.append(author.group()[6:])
                else:
                    self.author_list.append('')
                for tag_time in tag.find_all('div', class_='header'):
                    time = time_p.search(str(tag_time))
                    if time:
                        self.time_list.append(time.group()[6:])
                    else:
                        self.time_list.append('')

        my_bool = True
        for tag in soup.find_all('div', style='padding-bottom:10px;'):
            for tag_title in tag.find_all('a', class_='list subject'):
                if my_bool:
                    title = title_p.search(str(tag_title))
                    if title:
                        self.title_list.append(title.group()[7:-1])
                        my_bool = False
                    else:
                        self.title_list.append('')
                        my_bool = False
                else:
                    flag = flag_p.search(str(tag_title))
                    if flag:
                        self.flag_list.append(flag.group()[7:-1])
                        my_bool = True
                    else:
                        self.flag_list.append('')
                        my_bool = True

    def insert_into_db(self):
        mydb = Mysql()
        cur = mydb.conn.cursor()
        length = len(self.author_list)

        for num_flag in range(0, length):
            self.title_list[num_flag] = '"' + self.title_list[num_flag] + '"'
            self.flag_list[num_flag] = '"' + self.flag_list[num_flag] + '"'
            sql = 'insert into gitblit values('"%s"', '"%s"', '"%s"', '"%s"')' % \
                  (self.author_list[num_flag], self.time_list[num_flag],
                   self.title_list[num_flag], self.flag_list[num_flag])
            try:
                print sql
                cur.execute(sql)
            except Exception, e:
                print Exception, ":", e
                cur.close()
                mydb.conn.commit()
                mydb.conn.close()

        cur.close()
        mydb.conn.commit()
        mydb.conn.close()


class Mysql(object):
    def __init__(self):
        self.conn = MySQLdb.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='zx',
            db='GITBLIT',
            charset='utf8'
        )

    def create(self):
        cur = self.conn.cursor()
        cur.execute('create table gitblit(author varchar(20), time varchar(32), title varchar(128), '
                    'flag varchar(20)')
        cur.close()
        self.conn.commit()
        self.conn.close()


def main():
    spider = Spider()
    spider.get_page()
    spider.insert_into_db()

if __name__ == '__main__':
    main()