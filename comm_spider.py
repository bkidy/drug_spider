from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import re
import socket


class Drug:
    def __init__(self):
        self.clint = MongoClient('mongodb://localhost:27017')
        self.drug = self.clint.drug
        self.collection = self.drug['goods']
        self.comm_collection = self.drug['comments']

    def dbmodify(self):
        for data in self.collection.find({},{"goods_id":1,"goods_price":1}):
            try:
                _id = data['_id']
                id = data['goods_id'].split("：")[1]
                price = data['goods_price'].split("￥")[1]
                self.collection.update({'_id': _id},{'$set':{'goods_id':id,'goods_price':price}})
                print(_id, id, price)
            except IndexError:
                pass



    def getBaseArgument(self,goods_id):
        base_url = 'https://www.111.com.cn/interfaces/review/list/html.action'
        data = {
            'goodsId': goods_id,
            'pageIndex': 1,
            'score': '1&_19020301'
        }
        try:
            self.collection.update_one({'url_id': goods_id}, {'$set': {'commspider': True}})
            requests.packages.urllib3.disable_warnings()
            requests.adapters.DEFAULT_RETRIES = 5
            # 设置连接活跃状态为False
            s = requests.session()
            s.keep_alive = False
            r = s.get(base_url, params=data, timeout = 5,verify=False)
            r.close()
            soup = BeautifulSoup(r.text, 'html.parser')
            if soup.find_all("div", class_="view_no_result"):
                return "No Comments!"
            else:
                total_page_text = soup.find_all(text=re.compile(r'共\d+页'))[0]
                pattern = re.compile(r'\d+')
                total_page = pattern.findall(total_page_text)
                return total_page[0]
        except requests.exceptions.RequestException as e:
            print(e)

    def getCommlist(self,goods_id, total_page):
        base_url = 'https://www.111.com.cn/interfaces/review/list/html.action'
        try:
            for i in range(1, int(total_page)):
                data = {
                    'goodsId': goods_id,
                    'pageIndex': i,
                    'score': '1&_19020301'
                }
                try:
                    requests.packages.urllib3.disable_warnings()
                    requests.adapters.DEFAULT_RETRIES = 15
                    # 设置连接活跃状态为False
                    s = requests.session()
                    s.keep_alive = False
                    r = s.get(base_url, params=data, timeout = 5,verify=False)
                    r.close()
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for tr in soup.find_all("tr"):
                        comments = {}
                        try:
                            comments['goodsId'] = goods_id
                            comments['content'] = tr.find('p').text.strip()
                            comments['date'] = tr.find('p', attrs={'class': 'eval_date'}).text.strip()
                            self.comm_collection.insert_one(comments)
                        except:
                            print(goods_id + "Have some problem!\n")
                        print(comments)
                except requests.exceptions.RequestException as e:
                    print(e)
        except ValueError:
            return "No Comments! Try next!"

    def getComments(self):
        i = 0
        goods_list = []
        for data in self.collection.find({'commspider': False}, {"url_id"}):
            id = data['url_id']
            goods_list.append(id)
        length = len(goods_list)
        print("总共 {} 条商品".format(length))
        for good in goods_list:
            total_page = self.getBaseArgument(good)
            comments = self.getCommlist(good,total_page)
            i = i + 1
            print("总共 {} 条商品\n目前第 {} 条\n商品编号 {} \n".format(length,i, good))
            print(comments)


test = Drug().getComments()