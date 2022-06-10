# -*- coding: utf-8 -*-
"""
@desc: 搜狗拼音词库
@version: python3
@author: shhx
@time: 2022/4/11 10:03
"""
import time
import os
from urllib.parse import urljoin, urlsplit, parse_qs, unquote
from pyquery import PyQuery as pq
import scrapy
from scrapy.http import Response
from app.items.file_download import FileItem


def get_next_url(doc: pq, next_label="a", next_text="下一页"):
    """
    获取翻页的url
    :param doc:
    :param next_label:
    :param next_text:
    :return:
    """
    for a_ii in doc.find(next_label).items():
        if a_ii.text() == next_text:
            return a_ii.attr("href")
    return ""


class A(scrapy.Spider):
    """
    下载 词库
    """

    name = "sogou"
    url_root = "https://pinyin.sogou.com/dict/cate/index/"
    custom_settings = {
        "ITEM_PIPELINES": {
            "app.pipelines.file_download.FileDownloadPipeline": 1,
        },
        "FILES_STORE": "./搜狗词库",
    }
    exist_ids = set([])

    def start_requests(self):
        self.update_exist_ids()
        # 通过清单提供 分类名称
        urls_index = [
            {"id_name": "城市信息", "id": "167", "city": True},
            {"id_name": "自然科学", "id": "1"},
            {"id_name": "社会科学", "id": "76"},
            {"id_name": "工程应用", "id": "96"},
            {"id_name": "农林渔畜", "id": "127"},
            {"id_name": "医学医药", "id": "132"},
            {"id_name": "电子游戏", "id": "436"},
            {"id_name": "艺术设计", "id": "154"},
            {"id_name": "生活百科", "id": "389"},
            {"id_name": "运动休闲", "id": "367"},
            {"id_name": "人文科学", "id": "31"},
            {"id_name": "娱乐休闲", "id": "403"},
        ]
        for each in urls_index:
            url = urljoin(self.url_root, each["id"])
            if each.get("city"):
                yield scrapy.Request(
                    url=url, callback=self.parse_city, meta=each
                )
            else:
                yield scrapy.Request(url=url, callback=self.parse, meta=each)

    def parse(self, response: Response):
        """
        列表页信息
        :param response:
        :return:
        """
        meta = response.meta
        doc = pq(response.body)
        for a_ii in doc("div[class=dict_dl_btn]").find("a").items():
            a_href = a_ii.attr("href")
            qs_dict = parse_qs(urlsplit(a_href).query)
            ii_id = qs_dict["id"][0]
            ii_name = qs_dict["name"][0].replace("/", "_")
            item_dict = {
                "dir_name": meta["id_name"],
                "url": a_href,
                "file_name": f"{ii_id}-{ii_name}.scel",
            }
            if ii_id in self.exist_ids:
                continue
            yield FileItem(**item_dict)
        next_url = get_next_url(doc)
        if next_url:
            yield response.follow(next_url, callback=self.parse, meta=meta)

    def parse_city(self, response: Response):
        """
        获取城市信息
        :param response:
        :return:
        """
        doc = pq(response.body)
        # 城市信息类
        for a_ii in doc("div[id=city_list_show]").find("a").items():
            yield response.follow(
                a_ii.attr("href"), callback=self.parse, meta=response.meta
            )

    def update_exist_ids(self):
        """
        获取已存在的文件id
        :return:
        """
        file_dir = self.custom_settings.get("FILES_STORE")
        if not os.path.isdir(file_dir):
            return
        for each_type in os.listdir(file_dir):
            each_path = os.path.join(file_dir, each_type)
            if not os.path.isdir(each_path):
                continue
            for filename in os.listdir(each_path):
                self.exist_ids.add(filename.split("-")[0])


class B(scrapy.Spider):
    """
    词库清单，用于统计核对
    """

    name = "sogou_info"
    # 城市信息-全国，在城市列表中获取词库列表即可
    start_urls = ["https://pinyin.sogou.com/dict/cate/index/"]
    custom_settings = {
        "ITEM_PIPELINES": {"app.pipelines.file_save.ExcelPipeline": 1},
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
            "output_path": f"./搜狗词库/{time.time()}.xlsx",
        },
    }

    def parse(self, response: Response):
        doc = pq(response.body)
        # 大类
        for a_ii in doc("div[id=dict_nav_list]").find("a").items():
            yield response.follow(a_ii.attr("href"), callback=self.parse_list)
        # 城市信息类
        for a_ii in doc("div[id=city_list_show]").find("a").items():
            yield response.follow(a_ii.attr("href"), callback=self.parse_list)

    def parse_list(self, response):
        doc = pq(response.body)
        type_id = response.url.split("/default/")[0].split("/index/")[-1]
        type_name = doc("div[class=cate_title]").text()
        for row in doc("div[class=dict_detail_title_block]").items():
            row_show = row.parent()("div[class=dict_detail_show]")
            # 词库名
            cate_title_a = list(row.find("a").items())[0]
            # 词库示例
            show_content = list(
                row_show.find("div[class=show_content]").items()
            )
            row_dict = {
                "type_id": type_id,
                "type_name": type_name,
                "cate_name": cate_title_a.text(),
                "cate_url": response.urljoin(cate_title_a.attr("href")),
                "cate_demo": show_content[0].text(),
                "cate_count": show_content[1].text(),
                "cate_time": show_content[2].text(),
                "download_url": unquote(
                    row_show("div[class=dict_dl_btn] >a").attr("href")
                ),
            }
            row_dict["cate_id"] = row_dict["cate_url"].split("/index/")[-1]
            yield row_dict

        next_url = get_next_url(doc)
        if next_url:
            yield response.follow(next_url, callback=self.parse_list)
