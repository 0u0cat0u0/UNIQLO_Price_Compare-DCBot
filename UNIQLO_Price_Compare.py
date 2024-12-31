import discord
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

DISCORDTOKEN = ''

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
    if re.compile('!help',re.IGNORECASE).match(userMessage) or re.compile('!h').match(userMessage): #re.compile尋找開頭完全符合的字串，re.IGNORECASE忽略大小寫
        await message.channel.send('輸入商品代號或貼上商品網址')

    #用商品代號查詢價格
    elif re.match(r'\d{6}', userMessage):
        await message.channel.send(priceCompareID(userMessage))

    #用商品網址查詢價格
    elif re.match(r'https://www\.uniqlo\.com/tw/zh_TW/product-detail\.html\?productCode=.*', userMessage) or re.match(r'https://www\.uniqlo\.com/jp/ja/products/E.*', userMessage):
        await message.channel.send(priceCompareURL(userMessage))

#-----子函式-----

#查詢台灣價格和日本價格並回傳，呼叫查詢台灣價格、日本價格，最後呼叫查詢匯率，把日幣換算成台幣
def priceCompareID(productID):
    twPrice = searchTWProductPrice(productID)
    if twPrice == -1:
        return '台灣UNIQLO找不到此商品'
    
    jpPrice = searchJPProductPrice(productID)
    if jpPrice == -1:
        return '日本UNIQLO找不到此商品'

    twURL = 'https://www.uniqlo.com/tw/zh_TW/search.html?description=' + productID
    jpURL = 'https://www.uniqlo.com/jp/ja/search?q=' + productID
    comparison = '台灣價格：' + str(twPrice) + ', 日本價格：' + str(jpPrice) + ', 價差：' + str(abs(twPrice - jpPrice))

    #比較台灣價格和日本價格，如果日本價格比較低，回傳日本網址，反之回傳台灣網址
    if twPrice < jpPrice:
        comparison += '\n台灣UNIQLO網址：\n' + twURL
    else:
        comparison += '\n日本UNIQLO網址：\n' + jpURL
    return comparison

#查詢台灣價格和日本價格並回傳，呼叫查詢台灣價格或日本價格，如果式日幣就查詢匯率，把日幣換算成台幣
def priceCompareURL(url):
    if re.match(r'https://www\.uniqlo\.com/tw/zh_TW/product-detail\.html\?productCode=.*', url):
        productID = convertTWURL(url)
        price = searchJPProductPrice(productID)
        productURL = 'https://www.uniqlo.com/jp/ja/search?q=' + productID
        comparision = '日本'
    elif re.match(r'https://www\.uniqlo\.com/jp/ja/products/E.*', url):
        productID = convertJPURL(url)
        price = searchTWProductPrice(productID)
        productURL = 'https://www.uniqlo.com/tw/zh_TW/search.html?description=' + productID
        comparision = '台灣'

    if price == -1:
        comparision += 'UNIQLO無此商品'
    else:
        comparision += '價格：' + str(price) + '\n商品網址：\n' + productURL
    return comparision

#用商品ID查詢台灣價格，回傳int，回傳int，如果找不到商品回傳-1
def searchTWProductPrice(productID):
    try:
        url = 'https://www.uniqlo.com/tw/zh_TW/search.html?description=' + productID
        options = Options()
        options.headless = True    #設定為True可以在後台運行Chrome
        service = Service(ChromeDriverManager().install())  #安裝ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)  #等待10秒，讓網頁載入
        driver.get(url)
        price = driver.find_element(By.XPATH, '/html/body/div[2]/div/div[1]/div[2]/div/div/div/div/div[5]/div/div[1]/ul/li/div/a/div/div[2]/div[2]/div[3]/span').text  #用selenium套件查詢特定class，找到價格
        driver.quit()   #關閉瀏覽器
        return int(re.sub(r'\D', '', price))    #用re.sub去掉價格中的非數字部分
    except:
        return -1   #找不到商品回傳-1

#用商品ID查詢日本價格，換匯成台幣，回傳int，如果找不到商品回傳-1
def searchJPProductPrice(productID):
    try:
        url = 'https://www.uniqlo.com/jp/ja/search?q=' + productID
        options = Options()
        options.headless = True
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service = service, options = options)
        driver.implicitly_wait(10)
        driver.get(url)
        price = driver.find_element(By.XPATH, '/html/body/div[1]/section[1]/div[2]/section/div/div[2]/div/div[1]/div[1]/div/div/a/div[2]/div[2]/div/div[1]/div/p').text
        driver.quit()
        return searchExchangeRate(int(re.sub(r'\D', '', price)))
    except:
        return -1

#查詢匯率，回傳int
def searchExchangeRate(productPrice):
    currencyToChange = 'JPY'   #要換的貨幣
    currencyChangeTo = 'TWD'   #要換成的貨幣
    #呼叫Yahoo Finance API查詢匯率
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + currencyToChange + currencyChangeTo + '=X?includePrePost=false&interval=1d&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'
    headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    html = requests.get(url, headers=headers)
    data = html.json()
    exchangeRate = data['chart']['result'][0]['meta']['regularMarketPrice']
    return int(float(productPrice) * float(exchangeRate))

#把台灣商品網址轉換成商品ID，回傳str
def convertTWURL(url):
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = service, options = options)
    driver.implicitly_wait(10)
    driver.get(url)
    productID = driver.find_element(By.XPATH, '/html/body/div[2]/div/div[1]/div[2]/div/div/div/div/div[1]/div[4]/div[2]/div/div[1]/div[1]').text
    driver.quit()
    return re.sub(r'\D', '', productID)

#把日本商品網址轉換成商品ID，回傳str
def convertJPURL(url):
    productID = re.search(r'\d{6}', url).group(0)    #用re.serach.group回傳找到符合規則的6位數字串
    return productID

client.run(DISCORDTOKEN)