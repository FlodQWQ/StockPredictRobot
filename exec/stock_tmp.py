from datetime import datetime
import json

import akshare as ak
import pandas as pd

import os


class StockTmp:
    def __init__(self):
        self.stock_spot_df = None

    def init(self):
        current_date = datetime.now().strftime("%Y_%m_%d")
        if os.path.exists(f"./tmp/{current_date}.json"):
            try:
                with open(f"./tmp/{current_date}.json", 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                self.stock_spot_df = pd.DataFrame(json_data)
                return "股票数据初始化成功,来源:本地缓存"
            except:
                os.remove(f"./tmp/{current_date}.json")
                self.init()
        else:
            try:
                self.delete_tmp("./tmp")
                stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
                stock_hk_spot_em_df = ak.stock_hk_spot_em()
                self.stock_spot_df = pd.concat([stock_zh_a_spot_em_df, stock_hk_spot_em_df])
                json_data = self.stock_spot_df.to_json(orient='records', force_ascii=False)
                with open(f"./tmp/{current_date}.json", 'w', encoding='utf-8') as f:
                    f.write(json_data)
                return "股票数据初始化成功,来源:API接口"
            except:
                return "股票数据初始化失败，请检查网络连接"

    def search_stock(self, data):
        if data.isdigit():
            search = self.stock_spot_df[self.stock_spot_df['代码'] == data]
        else:
            search = self.stock_spot_df[self.stock_spot_df['名称'].str.contains(data)]
        return search

    def delete_tmp(self, directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
