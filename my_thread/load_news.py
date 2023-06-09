import time
from threading import Lock

from PyQt5.QtCore import QThread, pyqtSignal

from config import *
from utils.request_mode import get_content
from utils.selenium_mode import SeleniumMode
from utils.llm_mode import SemanticKernel


class ThreadLoadNews(QThread):
    begin = pyqtSignal(str)
    send = pyqtSignal(list)
    end = pyqtSignal(str)

    def __init__(self, company_name, search_cnt):
        super(QThread, self).__init__()
        self.company_name = company_name
        self.search_cnt = search_cnt

    def get_news(self):
        try:
            return get_content(self.company_name, self.search_cnt)
        except:
            return [ERROR_CODE]

    def run(self):
        self.begin.emit("开始获取新闻列表...")
        self.send.emit(self.get_news())
        self.end.emit("获取新闻列表完成!")


class ThreadGetNewsContents(QThread):
    begin = pyqtSignal(str)
    processing = pyqtSignal(int)
    send = pyqtSignal(list)
    end = pyqtSignal(str)

    def __init__(self, urls: list):
        super(QThread, self).__init__()
        self.urls = urls
        self.contents = []
        self.t_cnt = 0
        self.t_finished = 0
        self.lock = Lock()
        # for _ in range(MAX_CONNECTIONS):
        #     self.pools.append(SeleniumMode())

    def receive_content(self, content):
        self.lock.acquire()
        # print(content[0])
        self.contents.append(content)
        self.t_cnt -= 1
        self.lock.release()
        self.t_finished += 1

    def run(self):
        self.begin.emit("开始获取网页内容...")
        # print(self.urls)
        for cnt, url in enumerate(self.urls):
            while self.t_cnt >= MAX_CONNECTIONS:
                time.sleep(0.1)
            tmp_thread = ThreadSelenium(url[0], url[1][0])
            tmp_thread.content.connect(self.receive_content)
            tmp_thread.start()
            self.lock.acquire()
            self.t_cnt += 1
            self.lock.release()
            self.processing.emit(cnt + 1)
        while self.t_cnt > 0 or self.t_finished < len(self.urls):
            time.sleep(1)
        self.send.emit(self.contents)
        self.end.emit("获取网页内容完成!")


class ThreadSelenium(QThread):
    content = pyqtSignal(list)

    def __init__(self, no, url):
        super(QThread, self).__init__()
        self.selenium_ = SeleniumMode()
        self.no = no
        self.url = url

    def run(self) -> None:
        try:
            # print(self.url)
            ans = self.selenium_.get_content(self.url)
            self.content.emit([self.no, ans])
        except:
            self.content.emit([self.no, "ERROR"])


class ThreadScoreNews(QThread):
    begin = pyqtSignal(str)
    processing = pyqtSignal(int)
    send = pyqtSignal(list)
    end = pyqtSignal(str)

    def __init__(self, web_contents: list, temperature: float, company_name: str, term: int):
        super(QThread, self).__init__()
        self.sk = SemanticKernel()
        self.web_contents = web_contents
        self.temperature = temperature
        self.company_name = company_name
        self.term = term

    def run(self):
        self.begin.emit("开始根据网页提取新闻内容并评分...")
        news_contents = []
        for cnt, content in enumerate(self.web_contents):
            self.processing.emit(cnt + 1)
            # print(content)
            news_content = self.sk.extract_html(content[1])
            # print(news_content)
            news_score = self.sk.score_news(news_content, self.temperature, self.company_name, self.term)
            # print(news_score)
            self.send.emit([content[0], str(news_content), str(news_score)])
        self.end.emit("评分完成!")
