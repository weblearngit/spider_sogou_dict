# -*- coding: utf-8 -*-
"""
@desc: 结果保存到excel中
@version: python3
@author: shhx
@time: 2022/4/11 17:35
"""
import os
import json
from openpyxl import Workbook


def mkdir_for_filepath(file_path):
    save_dir = os.path.dirname(file_path)
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)


class ExcelPipeline(object):
    def __init__(self, save_info):
        self.file_output_path = save_info["output_path"]
        self.excel_titles = []
        self.excel_val_keys = []
        for each in save_info["title"]:
            self.excel_titles.append(each["name"])
            self.excel_val_keys.append(each["value"])
        self.content = []

    @classmethod
    def from_crawler(cls, crawler):
        """
        获取spider的settings参数,返回Pipeline实例对象
        "EXCEL_SAVE": {
            "title": [
                {"name": "id", "value": "cate_id"},
                {"name": "分类名", "value": "type_name"},
                {"name": "词库名", "value": "cate_name"},
                {"name": "更新时间", "value": "cate_time"},
                {"name": "词条样例", "value": "cate_demo"},
                {"name": "已下载次数", "value": "cate_count"},
                {"name": "分类id", "value": "type_id"},
                {"name": "详情页", "value": "cate_url"},
                {"name": "下载url", "value": "download_url"},
            ],
            "output_path": f"M:/z_corpus/搜狗词库/{time.time()}.xlsx",
        },
        """
        save_info = crawler.settings["EXCEL_SAVE"]
        return cls(save_info)

    def process_item(self, item, spider):
        # 把数据的每一项整理出来
        line = []
        for key in self.excel_val_keys:
            val = item.get(key, "")
            if isinstance(val, (list, tuple, dict)):
                val = json.dumps(val, ensure_ascii=False)
            line.append(val)
        self.content.append(line)
        return item

    def close_spider(self, spider):
        """
        spider关闭时调用
        """
        if not self.content:
            return
        # 创建excel, 填写表头
        wb = Workbook()
        ws = wb.active
        # 设置表头 ['ID', '标题', 'URL']
        ws.append(self.excel_titles)
        for line in self.content:
            # 将数据以行的形式添加到xlsx中
            ws.append(line)
        # 保存xlsx文件中
        mkdir_for_filepath(self.file_output_path)
        wb.save(self.file_output_path)


class TxtPipeline(object):
    def __init__(self, save_info):
        self.file_output_path = save_info["output_path"]
        self.flush_len = save_info.get("flush_data_length", 100)
        self.content = []

    @classmethod
    def from_crawler(cls, crawler):
        """
        获取spider的settings参数,返回Pipeline实例对象
        "TXT_SAVE": {
            "output_path": f"M:/z_corpus/搜狗词库/{time.time()}.txt",
            "flush_data_length": 100,
        },
        """
        save_info = crawler.settings["TXT_SAVE"]
        return cls(save_info)

    def process_item(self, item, spider):
        self._flush_data()
        line = json.dumps(item, ensure_ascii=False)
        self.content.append(line + "\n")
        return item

    def _save_data(self, content):
        mkdir_for_filepath(self.file_output_path)
        open(
            self.file_output_path, "a", encoding="utf8", newline=""
        ).writelines(content)

    def _flush_data(self):
        if len(self.content) > self.flush_len:
            self._save_data(self.content[: self.flush_len])
            del self.content[: self.flush_len]

    def close_spider(self, spider):
        """
        spider关闭时调用
        """
        if not self.content:
            return
        self._save_data(self.content)
