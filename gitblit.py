# coding=utf-8

from bs4 import BeautifulSoup
import urllib2
import re
import MySQLdb

URL = 'http://127.0.0.1:8080/repositories/'
RES_MATCH = r'summary/.*.git'
COM_MATCH = r'/commit.*;'
CODE_MATCH = r'/blob.*;'
AUTHOR_MATCH = r'title=".*"'
TIME_MATCH = r'>.*<'
TITLE_MATCH = r'>.*</a'
SOURCE_MATCH = r'line">.*</span></div> <'


class Spider(object):
    def __init__(self):
        self.get_repositories_list = []
        self.get_commits_list = []
        self.get_code_list = []
        self.final_dict = {'Author': '', 'Time': '', 'Title': '', 'Url': '', 'Source': ''}
        self.final_list = []

    def get_repositories(self):
        page = urllib2.urlopen(URL)
        contents = page.read()
        soup = BeautifulSoup(contents)
        res_p = re.compile(RES_MATCH)
        for tag in soup.find_all('a', class_='list'):
            res = res_p.search(str(tag))
            if res:
                if res.group().find(';') != -1:
                    self.get_repositories_list.append(res.group()[7:res.group().find(';')])
                else:
                    self.get_repositories_list.append(res.group()[7:])
        self.get_repositories_list[0] = '/gitolite'

    def get_commits(self):
        num = 1
        my_bool = True
        for flag in self.get_repositories_list:
            #my_bool = True
            while my_bool:
                commits_url = 'http://127.0.0.1:8080/log' + str(flag) + '?pg=' + str(num)
                num += 1
                page = urllib2.urlopen(commits_url)
                contents = page.read()
                soup = BeautifulSoup(contents)
                for quit_flag in soup.find_all('div', style='padding-bottom:5px;'):
                    if str(quit_flag).find('<span><em>next') != -1:
                        my_bool = False
                com_p = re.compile(COM_MATCH)
                for tag in soup.find_all('a', class_='list subject'):
                    com = com_p.search(str(tag))
                    if com:
                        pos = com.group().find(';')
                        if pos != -1:
                            self.get_commits_list.append(com.group()[:pos])

    def get_code(self):
        for flag in self.get_commits_list:
            code_url = 'http://127.0.0.1:8080' + str(flag)
            page = urllib2.urlopen(code_url)
            contents = page.read()
            soup = BeautifulSoup(contents)
            code_p = re.compile(CODE_MATCH)
            for tag in soup.find_all('a', class_='list'):
                code = code_p.search(str(tag))
                if code:
                    pos = code.group().find(';')
                    if pos != -1:
                        self.get_code_list.append(code.group()[:pos])

    def get_detail(self):
        self.get_code_list = list(set(self.get_code_list))
        for flag in self.get_code_list:
            detail_url = 'http://127.0.0.1:8080' + str(flag)
            self.final_dict['Url'] = detail_url
            page = urllib2.urlopen(detail_url)
            contents = page.read()
            soup = BeautifulSoup(contents)
            au_p = re.compile(AUTHOR_MATCH)
            for tag_au in soup.find_all('img', class_='gravatar'):
                author = au_p.search(str(tag_au))
                if author:
                    self.final_dict['Author'] = author.group()[7:-1]
                    tag_time = soup.find_all('span', class_='age4')
                    time_p = re.compile(TIME_MATCH)
                    my_time = time_p.search(str(tag_time))
                    if my_time:
                        self.final_dict['Time'] = my_time.group()[1:-1]
                        tag_title = soup.find_all('a', class_='title')
                        title_p = re.compile(TITLE_MATCH)
                        title = title_p.search(str(tag_title))
                        if title:
                            self.final_dict['Title'] = title.group()[1:-3]
                            tag_source = soup.find_all('div', class_='sourceview')
                            source_p = re.compile(SOURCE_MATCH)
                            source = source_p.search(str(tag_source))
                            if source:
                                self.final_dict['Source'] = source.group()[6:-15]
                self.insert_into_db()

    def insert_into_db(self):
        mysql = Mysql()
        cur = mysql.conn.cursor()
        self.final_dict['Author'] = '"' + self.final_dict['Author'] + '"'
        self.final_dict['Time'] = '"' + self.final_dict['Time'] + '"'
        self.final_dict['Title'] = '"' + self.final_dict['Title'] + '"'
        self.final_dict['Source'] = '"' + self.final_dict['Source'] + '"'
        sql = 'insert into gitblit values('"%s"', '"%s"', '"%s"', '"%s"')' % (self.final_dict['Author'],
                                                                 self.final_dict['Time'],
                                                                 self.final_dict['Title'],
                                                                 self.final_dict['Source'])
        try:
            cur.execute(sql)
        except Exception, e:
            print Exception, ":", e
            cur.close()
            mysql.conn.commit()
            mysql.conn.close()
        finally:
            cur.close()
            mysql.conn.commit()
            mysql.conn.close()


class Mysql(object):
    def __init__(self):
        self.conn = MySQLdb.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='zx',
            db='GITBLIT',
        )

    def create(self):
        cur = self.conn.cursor()
        cur.execute('create table gitblit(author varchar(20), time varchar(20), title varchar(32), '
                    'url varchar(64), source longtext)')
        cur.close()
        self.conn.commit()
        self.conn.close()


def main():
    spider = Spider()
    spider.get_repositories()
    spider.get_commits()
    spider.get_code()
    spider.get_detail()


if __name__ == '__main__':
    main()
