# -*- coding:utf-8 -*-
# import SougouSpider
import os
from bs4 import BeautifulSoup
from urllib.parse import unquote
import requests
import re

# 全类别下载（城市信息类比暂时不支持.）
# 全类别下载出现下载失败的情况，可能是网络不稳定，可以仅仅一个个类别的下载.
# Categories = [
#     '城市信息:167',
#     '自然科学:1',
#     '社会科学:76',
#     '工程应用:96',
#     '农林渔畜:127',
#     '医学医药:132',
#     '电子游戏:436',
#     '艺术设计:154',
#     '生活百科:389',
#     '运动休闲:367',
#     '人文科学:31',
#     '娱乐休闲:403']

# 可以注释部分类别，仅仅爬取自己需要的类比.
Categories = [
    # '城市信息:167',
    # '自然科学:1',
    # '社会科学:76',
    # '工程应用:96',
    # '农林渔畜:127',
    # '医学医药:132',
    # '电子游戏:436',
    # '艺术设计:154',
    # '生活百科:389',
    # '运动休闲:367',
    # '人文科学:31',
    '娱乐休闲:403']


def main(save_path: str):
    """搜狗词库下载"""
    sougou_spider = SougouSpider()
    # 创建保存路径
    try:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
    except Exception as e:
        print(e)
    # 我需要啥
    my_category_urls = []
    for mc in Categories:
        my_category_urls.append("https://pinyin.sogou.com/dict/cate/index/" + mc.split(":")[-1])
    print(my_category_urls)
    # 大类分类
    for index, category_one_url in enumerate(my_category_urls):
        # 创建保存路径
        category_one_path = save_path + "/" + Categories[index].split(":")[-1]
        try:
            if not os.path.exists(category_one_path):
                os.mkdir(category_one_path)
        except Exception as e:
            print(e)
        # 获取小类链接
        resp = sougou_spider.get_html(category_one_url)
        # 判断该链接是否为"城市信息",若是则采取Type1方法解析
        if category_one_url == "https://pinyin.sogou.com/dict/cate/index/167":
            category2_type1_urls = sougou_spider.get_category2_type1(resp)
        else:
            category2_type1_urls = sougou_spider.get_category2_type2(resp)
        # 小类分类
        for key, url in category2_type1_urls.items():
            # 创建保存路径
            category_two_path = category_one_path + "/" + key
            try:
                if not os.path.exists(category_two_path):
                    os.mkdir(category_two_path)
            except Exception as e:
                print(e)
            # 获取总页数
            try:
                resp = sougou_spider.get_html(url)
                pages = sougou_spider.get_page(resp)
            except Exception as e:
                print(e)
                pages = 1
            # 获取下载链接
            for page in range(1, pages + 1):
                page_url = url + "/default/" + str(page)
                resp = sougou_spider.get_html(page_url)
                download_urls = sougou_spider.get_download_list(resp)
                # 开始下载
                for keyDownload, url_download in download_urls.items():
                    file_path = category_two_path + "/" + keyDownload + ".scel"
                    if os.path.exists(file_path):
                        pass
                    else:
                        sougou_spider.download(url_download, file_path)
                        print(keyDownload + " 保存成功......")
    print("任务结束...")


class SougouSpider:

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def get_html(self, url, is_open_proxy=False, my_proxies=None):
        """
        获取Html页面
        :param is_open_proxy: 是否打开代理，默认否
        :param Proxies: 代理ip和端口，例如：103.109.58.242:8080，默认无
        :return:
        """
        try:
            pattern = re.compile(r'//(.*?)/')
            hostUrl = pattern.findall(url)[0]
            self.headers["Host"] = hostUrl
            if is_open_proxy:
                proxies = {"http": "http://" + my_proxies, }
                resp = requests.get(url, headers=self.headers, proxies=proxies, timeout=5)
            else:
                resp = requests.get(url, headers=self.headers, timeout=5)
            resp.encoding = resp.apparent_encoding
            # print("GetHtml成功..." + url)
            return resp
        except Exception as e:
            print("GetHtml失败..." + url)
            print(e)

    def get_category_one(self, resp):
        """获取大类链接"""
        category_one_urls = []
        soup = BeautifulSoup(resp.text, "html.parser")
        dict_nav = soup.find("div", id="dict_nav_list")
        dict_nav_lists = dict_nav.find_all("a")
        for dict_nav_list in dict_nav_lists:
            dict_nav_url = "https://pinyin.sogou.com" + dict_nav_list['href']
            category_one_urls.append(dict_nav_url)
        return category_one_urls

    def get_category2_type1(self, resp):
        """获取第一种类型的小类链接"""
        category2_type1_urls = {}
        soup = BeautifulSoup(resp.text, "html.parser")
        dict_td_lists = soup.find_all("div", class_="cate_no_child citylistcate no_select")
        for dict_td_list in dict_td_lists:
            dict_td_url = "https://pinyin.sogou.com" + dict_td_list.a['href']
            category2_type1_urls[dict_td_list.get_text().replace("\n", "")] = dict_td_url
        return category2_type1_urls

    def get_category2_type2(self, resp):
        """获取第二种类型的小类链接"""
        category2_type2_urls = {}
        soup = BeautifulSoup(resp.text, "html.parser")
        dict_td_lists = soup.find_all("div", class_="cate_no_child no_select")
        # 类型1解析
        for dict_td_list in dict_td_lists:
            dict_td_url = "https://pinyin.sogou.com" + dict_td_list.a['href']
            category2_type2_urls[dict_td_list.get_text().replace("\n", "")] = dict_td_url
        # 类型2解析
        dict_td_lists = soup.find_all("div", class_="cate_has_child no_select")
        for dict_td_list in dict_td_lists:
            dict_td_url = "https://pinyin.sogou.com" + dict_td_list.a['href']
            category2_type2_urls[dict_td_list.get_text().replace("\n", "")] = dict_td_url
        return category2_type2_urls

    def get_page(self, resp):
        """获取页码"""
        soup = BeautifulSoup(resp.text, "html.parser")
        dict_div_lists = soup.find("div", id="dict_page_list")
        dict_td_lists = dict_div_lists.find_all("a")
        page = dict_td_lists[-2].string
        return int(page)

    def get_download_list(self, resp):
        """获取下载链接"""
        download_urls = {}
        pattern = re.compile(r'name=(.*)')
        soup = BeautifulSoup(resp.text, "html.parser")
        dict_dl_lists = soup.find_all("div", class_="dict_dl_btn")
        for dict_dl_list in dict_dl_lists:
            dict_dl_url = dict_dl_list.a['href']
            dict_name = pattern.findall(dict_dl_url)[0]
            dict_ch_name = unquote(dict_name, 'utf-8').replace("/", "-").replace(",", "-").replace("|", "-") \
                .replace("\\", "-").replace("'", "-")
            download_urls[dict_ch_name] = dict_dl_url
        return download_urls

    def download(self, download_url, path, is_open_proxy=False, my_proxies=None):
        """下载"""
        pattern = re.compile(r'//(.*?)/')
        host_url = pattern.findall(download_url)[0]
        self.headers["Host"] = host_url
        if is_open_proxy:
            proxies = {"http": "http://" + my_proxies, }
            resp = requests.get(download_url, headers=self.headers, proxies=proxies, timeout=5)
        else:
            resp = requests.get(download_url, headers=self.headers, timeout=5)
        with open(path, "wb") as fw:
            fw.write(resp.content)
