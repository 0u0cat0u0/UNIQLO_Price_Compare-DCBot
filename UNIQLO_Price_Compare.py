import discord
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('>>Bot is online<<')

@client.event
async def on_message(message):
    userMessage = message.content #使用者輸入的訊息

    if message.author == client.user:
        return

    #幫助
    if re.compile('!help',re.IGNORECASE).match(userMessage) or re.compile('!h').match(userMessage): #re.IGNORECASE忽略大小寫
        await message.channel.send('輸入商品代號或貼上商品網址')

    #用商品代號查詢價格
    elif re.compile(r'\d{6}').match(userMessage):
        await message.channel.send(priceCompare(userMessage))

    #用台灣商品網址查詢價格
    elif re.compile(r'https://www.uniqlo.com/tw/zh_TW/product/').match(userMessage):
        await message.channel.send(priceCompare(userMessage))

#-----子函式-----

#查詢台灣價格和日本價格並回傳，呼叫查詢台灣價格、日本價格，最後呼叫查詢匯率，把日幣換算成台幣
async def priceCompare(productID):
    
    twPrice = searchTWProductPrice(productID)
    jpPrice = searchJPProductPrice(productID)
    
    if twPrice == -1:
        return '台灣UNIQLO找不到此商品'
    elif jpPrice == -1:
        return '日本UNIQLO找不到此商品'
    else:
        twURL = 'https://www.uniqlo.com/tw/zh_TW/search.html?description=' + productID
        jpURL = 'https://www.uniqlo.com/jp/ja/search?q=' + productID
        comparison = '台灣價格：' + str(twPrice) + ', 日本價格：' + str(jpPrice) + ', 價差：' + str(abs(twPrice - jpPrice))

        #比較台灣價格和日本價格，如果日本價格比較低，回傳日本網址，反之回傳台灣網址
        if twPrice < jpPrice:
            comparison += '\n台灣UNIQLO網址：\n' + twURL
        else:
            comparison += '\n日本UNIQLO網址：\n' + jpURL
        return comparison

#用商品ID查詢台灣價格，回傳int，回傳int，如果找不到商品回傳-1
async def searchTWProductPrice(productID):
    try:
        url = 'https://www.uniqlo.com/tw/zh_TW/search.html?description=' + productID
        options = Options()
        options.headless = True    #設定為True可以在後台運行Chrome
        service = Service(ChromeDriverManager().install())  #安裝ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(15)  #等待30秒，讓網頁載入
        driver.get(url)
        price = driver.find_element(By.CLASS_NAME, 'h-currency.bold').text  #用selenium套件查詢特定class，找到價格
        driver.quit()   #關閉瀏覽器
        return int(re.sub(r'\D', '', price))    #用re.sub去掉價格中的非數字部分
    except:
        return -1   #找不到商品回傳-1

#用商品ID查詢日本價格，換匯成台幣，回傳int，如果找不到商品回傳-1
async def searchJPProductPrice(productID):
    try:
        url = 'https://www.uniqlo.com/jp/ja/search?q=' + productID
        options = Options()
        options.headless = True
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service = service, options = options)
        driver.implicitly_wait(15)
        driver.get(url)
        price = driver.find_element(By.CLASS_NAME, 'fr-ec-price-text.fr-ec-price-text--middle.fr-ec-price-text--color-primary-dark.fr-ec-text-transform-normal').text
        driver.quit()
        return searchExchangeRate(int(re.sub(r'\D', '', price)))
    except:
        return -1

#查詢匯率，回傳int
async def searchExchangeRate(productPrice):
    currencyToChange = 'JPY'   #要換的貨幣
    currencyChangeTo = 'TWD'   #要換成的貨幣
    #呼叫Yahoo Finance API查詢匯率
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + currencyToChange + currencyChangeTo + '=X?includePrePost=false&interval=1d&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'
    headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    html = requests.get(url, headers=headers)
    data = html.json()
    exchangeRate = data['chart']['result'][0]['meta']['regularMarketPrice']
    return int(float(productPrice) * float(exchangeRate))

async def searchTWURL(url):
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = service, options = options)
    driver.implicitly_wait(15)
    driver.get(url)
    productID = driver.find_element(By.CLASS_NAME, 'product-detail-list-item.item-title-share-collect').text
    driver.quit()
    return re.sub(r'\D', '', productID)

client.run('')