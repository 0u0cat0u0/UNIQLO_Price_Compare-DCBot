import discord
import requests
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
    jpPrice = searchJPProductPrice(productID)
    #如果找不到商品就直接結束搜尋
    if jpPrice == -1:
        return '日本UNIQLO找不到此商品'

    twPrice = searchTWProductPrice(productID)
    if twPrice == -1:
        return '台灣UNIQLO找不到此商品'
    
    jpURL = convertJPIDToURL(productID)
    twURL = convertTWIDToURL(productID)
    comparison = '台灣價格：' + str(twPrice) + '\n日本價格：' + str(jpPrice) + '\n價差：' + str(abs(twPrice - jpPrice))

    #比較台灣價格和日本價格，如果日本價格比較低，回傳日本網址，反之回傳台灣網址
    if jpPrice < twPrice:
        comparison += '\n日本UNIQLO網址：\n' + jpURL
    else:
        comparison += '\n台灣UNIQLO網址：\n' + twURL
    return comparison

#查詢台灣價格和日本價格並回傳，呼叫查詢台灣價格或日本價格，如果是日幣就查詢匯率，把日幣換算成台幣
def priceCompareURL(productURL):
    if re.match(r'https://www\.uniqlo\.com/tw/zh_TW/product-detail\.html\?productCode=.*', productURL):
        productID = convertTWURLToID(productURL)
        price = searchJPProductPrice(productID)
        productURL = convertJPIDToURL(productID)
        comparision = '日本'
    elif re.match(r'https://www\.uniqlo\.com/jp/ja/products/E.*', productURL):
        productID = convertJPURLToID(productURL)
        price = searchTWProductPrice(productID)
        productURL = convertTWIDToURL(productID)
        comparision = '台灣'

    if price == -1:
        comparision += 'UNIQLO找不到此商品'
    else:
        comparision += '價格：' + str(price) + '\n商品網址：\n' + productURL
    return comparision

#用商品ID查詢台灣價格，回傳int，回傳int，如果找不到商品回傳-1，在需要查詢台灣UNIQLO價格時使用
def searchTWProductPrice(productID):
    try:
        url = 'https://d.uniqlo.com/tw/p/search/products/by-description'
        headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
        json = {
            'url':'/tw/zh_TW/search.html?description=' + productID,
            'pageInfo':{'page':1,'pageSize':24},
            'belongTo':'pc',
            'rank':'overall',
            'priceRange':{'low':0,'high':0},
            'color':[],
            'size':[],
            'identity':[],
            'exist':[],
            'searchFlag':True,
            'description':productID,
            'stockFilter':'warehouse'
        }
        html = requests.post(url, headers=headers, json=json, timeout=10)
        data = html.json()
        price = data['resp'][0]['productList'][0]['prices'][0]
        return int(price)    #用re.sub去掉價格中的非數字部分
    except:
        return -1   #找不到商品回傳-1

#用商品ID查詢日本價格，換匯成台幣，回傳int，如果找不到商品回傳-1，在需要查詢日本UNIQLO價格時使用    
def searchJPProductPrice(productID):
    try:
        url = 'https://www.uniqlo.com/jp/api/commerce/v5/ja/products?productIds=E' + productID + '-000'
        headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
        html = requests.get(url, headers=headers, timeout=10)
        data = html.json()
        price = data['result']['items'][0]['prices']['base']['value']
        return searchExchangeRate(int(price))
    except:
        return -1

#查詢匯率，回傳int，在需要把日幣換算成台幣時使用
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

#把台灣商品網址轉換成商品ID，回傳str，在輸入台灣商品網址時呼叫
def convertTWURLToID(productURL):
    productCode = re.sub(r'\D', '', productURL)     #用re.sub去掉非數字部分
    url = "https://d.uniqlo.com/tw/p/product/detail?productCode=u" + productCode
    header = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    html = requests.get(url, headers=header, timeout=10)
    data = html.json()
    productID = data['resp'][0]['spuInfo']['rows'][0]['name']
    return re.sub(r'\D', '', productID)

#把日本商品網址轉換成商品ID，回傳str，在輸入日本商品網址時呼叫
def convertJPURLToID(productURL):
    productID = re.search(r'\d{6}', productURL).group(0)    #用re.serach.group回傳找到符合規則的6位數字串
    return productID

#把商品ID轉換成台灣商品網址，回傳str，在需要查詢台灣商品網址時使用
def convertTWIDToURL(productID):
    try:
        url = 'https://d.uniqlo.com/tw/p/search/products/by-description'
        headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
        json = {
            'url':'/tw/zh_TW/search.html?description=' + productID,
            'pageInfo':{'page':1,'pageSize':24},
            'belongTo':'pc',
            'rank':'overall',
            'priceRange':{'low':0,'high':0},
            'color':[],
            'size':[],
            'identity':[],
            'exist':[],
            'searchFlag':True,
            'description':productID,
            'stockFilter':'warehouse'
        }
        html = requests.post(url, headers=headers, json=json, timeout=10)
        data = html.json()
        productCode = data["resp"][0]["productList"][0]["productCode"]
        return 'https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode=' + productCode
    except:
        return -1   #找不到商品回傳-1

#把商品ID轉換成日本商品網址，回傳str，在需要查詢日本商品網址時使用
def convertJPIDToURL(productID):
    return 'https://www.uniqlo.com/jp/ja/products/E' + productID

client.run(DISCORDTOKEN)