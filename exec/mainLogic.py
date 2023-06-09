import json
import sys
import time
from datetime import datetime, timedelta

from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QFileDialog
from qfluentwidgets import InfoBar, InfoBarPosition

from my_thread.load_stocks import ThreadLoadStocks
from my_thread.load_news import ThreadLoadNews, ThreadGetNewsContents, ThreadScoreNews
from my_thread.waiting import ThreadWaiting
from ui.main_ui import Ui_MainWindow
from config import *
from utils.preprocess_str import keep_json_format
from exec.chooseLogic import dialogUI
from utils.save_as_html import save_html


class mainUI(QMainWindow, Ui_MainWindow):
    exitSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        super(mainUI, self).__init__(parent)
        self.term = None
        self.company_name = None
        self.thread_waiting = None
        self.thread_load_stocks = ThreadLoadStocks()
        self.thread_load_news = None
        self.thread_acquire_news = None
        self.thread_extract_news = None
        self.dialog = dialogUI()
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.setWindowTitle('基于舆情的公司股价预测系统')
        sys.stdout = self
        self.stocks = None
        self.search_cnt = 0
        self.temperature = 0
        self.score = 0
        self.close_code = 0
        self.stock_code = 0
        self.init_widgets()
        self.bind_signals()
        self.init_stocks()
        self.news = {}
        self.news_lists = []
        self.html_contents = []
        self.news_contents = []

    def write(self, text):
        self.append_log(WAITING_CODE, text)

    def closeEvent(self, event):
        self.exitSignal.emit(self.close_code)

        super().closeEvent(event)

    def init_stocks(self):
        self.set_status(WAITING_CODE, "加载公司信息中...")
        self.thread_load_stocks.stock_tmp.connect(self.set_stocks)
        self.thread_load_stocks.msg.connect(self.load_stocks_end)
        self.thread_load_stocks.start()

    def set_stocks(self, stocks):
        self.stocks = stocks

    def load_stocks_end(self, msg: str):
        if "成功" in msg:
            self.append_log(SUCCESS_CODE, msg)
            self.set_status(SUCCESS_CODE, "等待输入公司名...")
        else:
            self.append_log(ERROR_CODE, msg)
            self.set_status(ERROR_CODE, "初始化公司失败")

    def init_widgets(self):
        self.slider_search_cnt.setValue(3)
        self.label_search_cnt.setText(str(self.slider_search_cnt.value() * 10))
        self.slider_temperature.setValue(80)
        self.label_tamperature.setText(str(self.slider_temperature.value() / 100))
        self.init_table()
        self.init_date_picker()
        self.init_logs()
        self.button_predict.setDisabled(True)
        self.button_save.setDisabled(True)
        self.progressbar_status.setVisible(False)
        # self.append_log(SUCCESS_CODE, self.stocks.init())
        self.dialog = dialogUI()

    def bind_signals(self):
        self.slider_search_cnt.valueChanged.connect(self.search_cnt_changed)
        self.slider_temperature.valueChanged.connect(self.temperature_changed)
        self.search_zone.returnPressed.connect(self.search)
        self.search_zone.searchButton.clicked.connect(self.search)
        self.button_predict.clicked.connect(self.predict)
        self.button_reset_all.clicked.connect(self.reset_all)
        self.button_save.clicked.connect(self.save_result)

    def init_date_picker(self):
        current_date = datetime.now()
        past_date = current_date - timedelta(days=14)
        self.date_picker.setDate(QDate(past_date.year, past_date.month, past_date.day))

    def init_logs(self):
        self.textedit_logs.setReadOnly(True)

    def init_table(self):
        self.result_tableview.setWordWrap(False)
        self.result_tableview.setRowCount(30)
        self.result_tableview.setColumnCount(5)
        self.result_tableview.verticalHeader().hide()
        self.result_tableview.setHorizontalHeaderLabels(['公司名', '新闻标题', '新闻评分', '评分理由', '新闻链接'])
        self.result_tableview.resizeColumnsToContents()
        self.result_tableview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_tableview.setSortingEnabled(True)
        self.setStyleSheet("Demo{background: rgb(249, 249, 249)} ")

    def search(self):
        res = self.stocks.search_stock(self.search_zone.text()).to_dict(orient='records')
        if len(res) == 0:
            self.error_info_bar("查找失败", "未找到相关公司,请确认输入是否正确")
        elif len(res) == 1:
            self.set_company(res[0]['名称'], res[0]['代码'], res[0]['最新价'])
        else:
            self.dialog.receive_data.emit(res)
            self.dialog.show()
            self.dialog.send_data.connect(self.receive_result)

    def predict(self):
        self.search_cnt = self.slider_search_cnt.value() * 10
        self.temperature = self.slider_temperature.value() / 100
        self.company_name = self.request_line.text()
        self.result_tableview.setRowCount(self.search_cnt)
        self.term = (datetime.now().date() - self.date_picker.date.toPyDate()).days
        self.thread_acquire_news = ThreadLoadNews(self.request_line.text(), int(self.search_cnt / 10))
        self.thread_acquire_news.begin.connect(self.load_news_begin)
        self.thread_acquire_news.end.connect(self.load_news_end)
        self.thread_acquire_news.send.connect(self.get_news_list)
        self.thread_acquire_news.start()

    def search_cnt_changed(self):
        self.label_search_cnt.setText(str(self.slider_search_cnt.value() * 10))

    def load_news_begin(self, content):
        self.set_status(WAITING_CODE, content)
        self.append_log(WAITING_CODE, content)

    def after_waiting_begin(self, content):
        self.set_status(WAITING_CODE, content)

    def load_news_end(self, content):
        try:
            self.update_table()
            self.set_status(SUCCESS_CODE, content)
            self.append_log(SUCCESS_CODE, f"{content},新闻条数:{len(self.news_lists)}")
            self.thread_waiting = ThreadWaiting("获取新闻网页", WAITING_TIME)
            self.thread_waiting.msg.connect(self.waiting_msg)
            self.thread_waiting.start()
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.set_status(ERROR_CODE, "获取新闻列表失败")
            self.append_log(ERROR_CODE, "获取新闻列表失败，请检查网络连接")
            self.append_log(ERROR_CODE, f"异常:{exc_type.__name__}")

    def get_news_end(self, content):
        try:
            self.thread_load_news.quit()
            self.set_status(SUCCESS_CODE, content)
            self.append_log(SUCCESS_CODE, f"{content},新闻条数:{len(self.html_contents)}")
            self.thread_waiting = ThreadWaiting("提取新闻内容", WAITING_TIME)
            self.thread_waiting.msg.connect(self.waiting_msg)
            self.thread_waiting.start()
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.set_status(ERROR_CODE, "提取新闻内容失败")
            self.append_log(ERROR_CODE, "提取新闻内容失败，请检查OPENAI_API_KEY是否正确")
            self.append_log(ERROR_CODE, f"异常:{exc_type.__name__}")

    def extract_news_end(self, content):
        try:
            with open(f'./results/{datetime.now().strftime("%Y_%m_%d")}_{self.company_name}.json', "w",
                      encoding="utf-8") as file:
                json.dump(self.news, file, ensure_ascii=False, indent=4)
            self.set_status(SUCCESS_CODE, content)
            self.append_log(SUCCESS_CODE, f"{content},新闻条数:{len(self.html_contents)}")
            self.set_final_score()
            self.button_save.setDisabled(False)

        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.set_status(ERROR_CODE, "保存评分结果失败")
            self.append_log(ERROR_CODE, "保存评分结果失败，请检查打分是否完成")
            self.append_log(ERROR_CODE, f"异常:{exc_type.__name__}")

    def waiting_msg(self, msg: str):
        if msg.startswith("等待"):
            self.append_log(WAITING_CODE, msg)
            self.set_status(WAITING_CODE, "等待中...")
        elif "获取新闻网页" in msg:
            self.append_log(SUCCESS_CODE, msg)
            self.set_status(WAITING_CODE, "获取新闻网页中...")
            self.thread_load_news = ThreadGetNewsContents(
                [(cnt, item) for cnt, item in enumerate(self.news_lists)])
            self.thread_load_news.begin.connect(self.after_waiting_begin)
            self.thread_load_news.send.connect(self.get_news)
            self.thread_load_news.processing.connect(self.get_news_processing)
            self.thread_load_news.end.connect(self.get_news_end)
            self.thread_load_news.start()
        elif "提取新闻内容" in msg:
            self.append_log(SUCCESS_CODE, msg)
            self.set_status(WAITING_CODE, "提取新闻内容并评分中...")
            self.thread_extract_news = ThreadScoreNews(
                [(cnt, item) for cnt, item in enumerate(self.html_contents)], self.temperature, self.company_name,
                self.term)
            self.thread_extract_news.begin.connect(self.after_waiting_begin)
            self.thread_extract_news.send.connect(self.score_news)
            self.thread_extract_news.processing.connect(self.extract_news_processing)
            self.thread_extract_news.end.connect(self.extract_news_end)
            self.thread_extract_news.start()

    def get_news_list(self, contents):
        self.news_lists = contents
        for (i, item) in enumerate(contents):
            self.news[i] = {}
            self.news[i]["name"] = self.request_line.text()
            self.news[i]["title"] = item[1][3:]
            self.news[i]["url"] = item[0]
            self.news[i]["score"] = 0
            self.news[i]["content"] = ""
            self.news[i]["reason"] = "TBD"

    def get_news(self, contents: list):
        for content in contents:
            self.news[content[0]]["content"] = content[1]
        for i in range(len(contents)):
            self.html_contents.append(self.news[i]["content"])

    def score_news(self, content):
        try:
            self.news_contents.append(content[1])
            self.news[content[0]]["summarize"] = keep_json_format(content[1])
            summarize_dict = keep_json_format(content[1])
            summarize_dict = json.loads(summarize_dict)
            self.news[content[0]]["date"] = summarize_dict["date"]
            self.news[content[0]]["content"] = summarize_dict["content"]
            ans_dict = json.loads(keep_json_format(content[2]))
            self.news[content[0]]["reason"] = ans_dict["reason"]
            self.news[content[0]]["score"] = ans_dict["mark"]
            self.score += ans_dict["mark"]
            self.update_table()
            self.append_log(SUCCESS_CODE, content[2])
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.news[content[0]]["summarize"] = "UNKNOWN"
            self.news[content[0]]["date"] = "UNKNOWN"
            self.news[content[0]]["content"] = "UNKNOWN"
            self.news[content[0]]["reason"] = "UNKNOWN"
            self.news[content[0]]["score"] = 0
            self.update_table()
            self.append_log(ERROR_CODE, "OpenAI 回答了预期格式外的答案，本条新闻被标记为UNKNOWN,请检查OPENAI_API_KEY是否正确或重试")
            self.append_log(ERROR_CODE, f"异常:{exc_type.__name__}")

    def get_news_processing(self, cnt):
        self.append_log(WAITING_CODE, f"获取网页中...第{cnt}/{len(self.news_lists)}条")

    def extract_news_processing(self, cnt):
        self.append_log(WAITING_CODE, f"提取新闻并评分中...第{cnt}/{len(self.html_contents)}条")

    def temperature_changed(self):
        self.label_tamperature.setText(str(self.slider_temperature.value() / 100))

    def set_status(self, status, content):
        if status == ERROR_CODE:
            self.progressbar_status.setVisible(False)
            self.progressbar_status.setMinimumWidth(0)
            self.progressbar_status.setMaximumWidth(0)
            self.label_status.setText(content)
        elif status == SUCCESS_CODE:
            self.progressbar_status.setVisible(False)
            self.progressbar_status.setMinimumWidth(0)
            self.progressbar_status.setMaximumWidth(0)
            self.label_status.setText(content)
        elif status == WAITING_CODE:
            self.progressbar_status.setVisible(True)
            self.progressbar_status.setMinimumWidth(0)
            self.progressbar_status.setMaximumWidth(200)
            self.label_status.setText(content)

    def set_company(self, company_name, stock_code, stock_price):
        self.label_company_name.setText(company_name)
        self.stock_code = stock_code
        self.label_stock_code.setText(stock_code)
        self.label_stock_price.setText(str(stock_price))
        self.append_log(SUCCESS_CODE, '公司信息获取成功')
        self.set_status(SUCCESS_CODE, '等待预测...')
        self.request_line.setText(company_name)
        self.button_predict.setEnabled(True)

    def append_log(self, status, content):
        color = "black"
        if status == ERROR_CODE:
            color = "red"
        elif status == SUCCESS_CODE:
            color = "green"
        if len(content) > 1:
            self.textedit_logs.append(
                f'<span style="color: {color};">[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] {content}</span>')
        scrollbar = self.textedit_logs.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_table(self):
        insert = []
        for i in range(self.search_cnt):
            insert.append(
                [self.news[i]["name"], self.news[i]["title"], str(self.news[i]["score"]), self.news[i]["reason"],
                 self.news[i]["url"]])
        insert += insert
        for i, newsInfo in enumerate(insert):
            for j in range(5):
                self.result_tableview.setItem(i, j, QTableWidgetItem(newsInfo[j]))
        self.result_tableview.resizeColumnsToContents()

    def save_result(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "保存评分结果",
                                                   f"{self.company_name} {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.html"
                                                   , "Html文件 (*.html);;所有文件 (*)",
                                                   options=options)
        infos = {
            "company_name": self.company_name,
            "stock_code": self.stock_code,
            "total_score": self.score,
            "predict_result": self.label_predict_result.text(),
        }

        if file_path:
            out = save_html(infos, self.news, file_path)
            if out.startswith("成功"):
                self.append_log(SUCCESS_CODE, out)
                self.set_status(SUCCESS_CODE, "保存成功")
            else:
                self.append_log(ERROR_CODE, out)
                self.set_status(ERROR_CODE, "保存失败")

    def set_final_score(self):
        self.label_final_score.setText(str(self.score))
        if self.score / self.search_cnt > 0.3:
            self.label_predict_result.setText("利好")
        elif self.score / self.search_cnt > 1:
            self.label_predict_result.setText("强烈利好")
        elif self.score / self.search_cnt < -0.3:
            self.label_predict_result.setText("利空")
        elif self.score / self.search_cnt < -1:
            self.label_predict_result.setText("强烈利空")
        else:
            self.label_predict_result.setText("中性")

    def error_info_bar(self, title, content):
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=3000,
            parent=self
        )

    def receive_result(self, data):
        if self.label_company_name.text() != data:
            self.search_zone.setText(data)
            self.search()

    def reset_all(self):
        self.close_code = 42
        self.close()
