import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


browser = webdriver.Chrome()
#browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
#browser.set_window_size(1100,900)
wait = WebDriverWait(browser,10)



def search():
    print('正在搜索')
    url = "https://www.taobao.com/"
    try:
        browser.get(url)
        # 输入框
        inputkeyword = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#q'))
        )
        # 提交按钮
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button'))
        )
        inputkeyword.clear()
        inputkeyword.send_keys(KEYWORD)
        submit.click()
        # 等待加载出100页
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total'))
        )
        # 等待页面加载完成在调用get_product()
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    print('正在翻页',page_number)
    try:
        # 输入框
        inputpage = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        # 提交按钮
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
            '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        inputpage.clear()
        inputpage.send_keys(page_number)
        submit.click()
        # 利用高亮的CSS选择器判断是否翻页成功
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR,
            '#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number))
        )
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    # 判断商品是否加载成功
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item'))
    )
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        #print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print("存储到MONGODB成功",result)
    except Exception:
        print("存储到MONGODB失败",result)


def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))# 提取出100
        for i in range(2,total+1):
            next_page(i)
    except Exception:
        print("抓取信息出错")
    finally:
        browser.close()


if __name__ == '__main__':
    main()
