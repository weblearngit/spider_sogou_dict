# -*- coding: utf-8 -*-
"""
@desc:
@version: python3
@author: shhx
@time: 2022/4/11 17:32
"""
import scrapy


class FileItem(scrapy.Item):
    """
    文件下载
    """

    dir_name = scrapy.Field()
    file_name = scrapy.Field()
    url = scrapy.Field()
