#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-02-02 08:59:40
# Project: oneDrug

from pyspider.libs.base_handler import *
from pymongo import MongoClient
import re


class Handler(BaseHandler):
    crawl_config = {
    }

    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017')
        self.drug = self.client.drug

    def insert_goods(self, data):
        collection = self.drug['goods']
        collection.update({'goods_id': data['goods_id']}, data, True)

    def insert_comments(self, data):
        collection = self.drug['comments']
        collection.insert_one(data)

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('https://www.111.com.cn/categories/', callback=self.categories_page, validate_cert=False,
                   fetch_type='js')

    @config(age=10 * 24 * 60 * 60)
    def categories_page(self, response):
        for each in response.doc('.allsort em > a').items():
            self.crawl(each.attr.href, callback=self.cagetory_list_page, validate_cert=False, fetch_type='js')

    @config(priority=1)
    def cagetory_list_page(self, response):
        for each in response.doc('#itemSearchList a[target="_blank"][class="product_pic pro_img"]').items():
            self.crawl(each.attr.href, callback=self.detail_page, validate_cert=False, fetch_type='js')
        next = response.doc('#search_table > div.turnPageBottom > a.page_next').attr.href
        self.crawl(next, callback=self.cagetory_list_page, validate_cert=False, fetch_type='js')

    @config(priority=2)
    def detail_page(self, response):
        goods_id = response.doc('#gallery_view > ul > li.item_number').text()
        cagetory_one = response.doc('body > div.wrap.clearfix > div > span:nth-child(3) > a').text()
        cagetory_two = response.doc('body > div.wrap.clearfix > div > span:nth-child(5) > a').text()
        cagetory_three = response.doc('body > div.wrap.clearfix > div > span:nth-child(7) > a').text()
        merchants = response.doc('div.middle_property > span:nth-child(1)').text()
        goods_name = response.doc('div.middle_property > h1').text()
        goods_desc = response.doc('div.middle_property > span.red.giftRed').text()
        goods_price = response.doc(
            'div.middle_property > div.shangpin_info > dl:nth-child(2) > dd > span.good_price').text()
        total_comments = response.doc('#fristReviewCount > span > a').text()

        brand = response.doc(
            '#tabCon > div:nth-child(1) > div.goods_intro > table > tbody > tr:nth-child(2) > td:nth-child(2)').text()
        spec = response.doc(
            '#tabCon > div:nth-child(1) > div.goods_intro > table > tbody > tr:nth-child(2) > td:nth-child(4)').text()
        weight = response.doc(
            '#tabCon > div:nth-child(1) > div.goods_intro > table > tbody > tr:nth-child(3) > td:nth-child(2)').text()
        manufacturers = response.doc(
            '#tabCon > div:nth-child(1) > div.goods_intro > table > tbody > tr:nth-child(3) > td:nth-child(4)').text()
        approval_number = response.doc(
            '#tabCon > div:nth-child(1) > div.goods_intro > table > tbody > tr:nth-child(4) > td:nth-child(2)').text()
        drug_type = response.doc(
            '#tabCon > div:nth-child(1) > div.goods_intro > table > tbody > tr:nth-child(4) > td:nth-child(4)').text()

        instructions = {}
        if response.doc('#prodDetailCotentDiv > table > tbody > tr:nth-child(1) > th').text():
            for i in range(3, 22):
                instructions_key = \
                response.doc('#prodDetailCotentDiv > table > tbody > tr:nth-child({}) > th'.format(i)).text().split(
                    " ")[0]
                instructions_value = response.doc(
                    '#prodDetailCotentDiv > table > tbody > tr:nth-child({}) > td'.format(i)).text()
                instructions[instructions_key] = instructions_value

        total_comments = response.doc('#itemComments > span').text()
        good_comments = response.doc('#productExperience > div > ul > li:nth-child(2) > a > span').text()
        mid_comments = response.doc('#productExperience > div > ul > li:nth-child(3) > a > span').text()
        bad_comments = response.doc('#productExperience > div > ul > li:nth-child(4) > a > span').text()

        url_id = re.findall('\d+', response.url)[1]

        goods_data = {
            'url_id': url_id,
            'goods_id': goods_id,
            'goods_name': goods_name,
            'goods_desc': goods_desc,
            'goods_price': goods_price,
            'merchants': merchants,
            'cagetory': {
                '1': cagetory_one,
                '2': cagetory_two,
                '3': cagetory_three
            },
            'drug_detail': {
                'brand': brand,
                'spec': spec,
                'weight': weight,
                'manufacturers': manufacturers,
                'approval_number': approval_number,
                'drug_type': drug_type
            },
            'instructions': instructions,
            'comments': {
                'total_comments': total_comments,
                'good_comments': good_comments,
                'mid_comments': mid_comments,
                'bad_comments': bad_comments
            }
        }
        self.insert_goods(goods_data)
