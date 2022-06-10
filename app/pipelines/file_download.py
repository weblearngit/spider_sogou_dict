# -*- coding: utf-8 -*-
"""
@desc:
@version: python3
@author: shhx
@time: 2022/4/11 12:51

需要同时配置 pipeline、FILES_STORE
    custom_settings = {
        'ITEM_PIPELINES': {
            'spiderapp.files.pipelines.FileDownloadPipeline': 1,
        },
        "FILES_STORE": 'E:/Z-TMP'
    }

如果需要判断不同的item，需要导入item，用isinstance(item, item_name)来判断
"""
from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request
from ..items.file_download import FileItem


class FileDownloadPipeline(FilesPipeline):
    def get_media_requests(self, item: FileItem, info):
        """
        获取item中的url，用于下载文件
        :param item:
        :param info:
        :return:
        """
        return Request(item["url"], meta=item)

    def file_path(self, request, response=None, info=None):
        """
        通过request匹配设置文件路径
        :param request:
        :param response:
        :param info:
        :return:
        """
        meta = request.meta
        return "%(dir_name)s/%(file_name)s" % meta
