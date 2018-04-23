# -*- coding:utf-8 -*-
from utlis.utlis import SpiderVariable
from lxml import etree
from bs4 import BeautifulSoup
import threading
from queue import Queue
import requests
import pymongo
import time


class CommentSpider(object):
    def __init__(self):
        self.url_list = ['https://movie.douban.com/top250?start=%s&filter=' % str(page) for page in range(0, 226, 25)]
        self.proxy_addr = SpiderVariable().get_random_proxy_addr()
        self.user_agent = SpiderVariable().get_random_user_agent()
        self.parse_role = "//ol[@class='grid_view']/li[1]//span[@class='title']"
        self.data_queue = Queue()
        self.headers = {
            "User-Agent": self.user_agent
        }

    def send_request(self, url):
        """
        request_url
        :param url: url address
        :return: response data
        """
        print url
        try:
            response = requests.get(url, proxies={'http': 'http://' + self.proxy_addr}, headers=self.headers)
            # 网络IO需要时间, 否则response为None, 存入队列
            self.data_queue.put(response)
            print response
            # time.sleep(1)
            # return response
        except Exception as e:
            print e

    def __open(self):
        """
        open mongoDB
        :return:
        """
        client = pymongo.MongoClient('mongodb://purity:mongodb@127.0.0.1:27017')
        db = client['myDB']
        collection = db['douban_movies_comment']
        return collection

    def save_mongo(self, data):
        collection = self.__open()
        collection.insert(data)

    def parse(self, response, parse_role):
        """
        xpath parse
        :param response:
        :param parse_role:
        :return:
        """
        html = etree.HTML(response)
        result = html.xpath(parse_role)
        return result

    def save_top_info(self, info_html):
        """
        set movie data
        :param info_html:
        :return:
        """
        movie_dict = {}
        soup = BeautifulSoup(info_html, 'lxml')
        # 电影海报
        movie_dict['img'] = soup.img['src']
        # 电影名
        movie_dict['title'] = soup.span.string
        # 电影主页URL
        movie_dict['movie_url'] = soup.a['href']
        # 电影人员
        movie_dict['worker'] = soup.find('p').contents[0].strip()
        # 电影时间/类型
        movie_dict['type'] = soup.find('p').contents[2].strip()
        # 评分
        movie_dict['score'] = soup.find('span', class_='rating_num').string
        try:
            movie_dict['quote'] = soup.find('span', class_='inq').string
        except Exception as e:
            pass
        return movie_dict

    def main(self):
        thread_list = []
        for url in self.url_list:
            t = threading.Thread(target=self.send_request, args=(url,))
            t.start()
            thread_list.append(t)
        # 网络IO需要时间, 需要时间
        time.sleep(1)

        # 取出队列内容
        response_list = []
        while not self.data_queue.empty():
            response_list.append(self.data_queue.get())

        # 对取出后的response进行操作
        for response in response_list:
            parse_ol = self.parse(response.content, "//*[@id='content']/div/div[1]/ol/li")
            for i in parse_ol:
                movie_dict = self.save_top_info(etree.tostring(i))
                self.save_mongo(movie_dict)


if __name__ == '__main__':
    spider = CommentSpider()
    spider.main()
