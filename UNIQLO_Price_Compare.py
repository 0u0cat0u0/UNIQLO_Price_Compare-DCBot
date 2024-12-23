import requests
import discord

intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('>>Bot is online<<')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    #幫助
    if message.content == 'help':
        await message.channel.send('買 標的 數量 價格\n'+
                                   '賣 標的 數量 價格\n'+
                                   '套利 usdt twd\n'+
                                   'BITO usdt twd\n'+
                                   'MAX usdt twd\n'+
                                   'EX usd twd\n'+
                                   'US tsm\n'+
                                   'TW 2330')

#----------查詢價格----------

    #BITO MAX 套利
    elif message.content.startswith('AR') or message.content.startswith('ar') or message.content.startswith('套利'):
        tmp = message.content.split(' ')
        url_BITO = 'https://api.bitopro.com/v3/tickers/'
        url_MAX = 'https://max-api.maicoin.com/api/v2/tickers/'
        html_BITO = requests.get(url_BITO+tmp[1]+'_'+tmp[2])
        html_MAX = requests.get(url_MAX+tmp[1]+tmp[2])

        await message.channel.send(arbitrage(tmp[2],tmp[1],html_BITO,html_MAX))

    #BITO 查詢價格
    elif message.content.startswith('BITO') or message.content.startswith('bito'):
        tmp = message.content.split(' ')

        await message.channel.send(get_price_BITO(tmp[1],tmp[2]))

    #MAX 查詢價格
    elif message.content.startswith('MAX') or message.content.startswith('max'):
        tmp = message.content.split(' ')
        
        await message.channel.send(get_price_MAX(tmp[1],tmp[2]))

    #yahoo finance 查詢外匯價格
    elif message.content.startswith('EX') or message.content.startswith('ex'):
        tmp = message.content.split(' ')
        
        await message.channel.send(get_price_Yahoo(tmp[1]+tmp[2],'=X',tmp[2]))

    #yahoo finance 查詢美股價格
    elif message.content.startswith('US') or message.content.startswith('us'):
        tmp = message.content.split(' ')
        
        await message.channel.send(get_price_Yahoo(tmp[1],'-USD','USD'))
    
    #yahoo finance 查詢台股價格
    elif message.content.startswith('TW') or message.content.startswith('tw'):
        tmp = message.content.split(' ')
        
        await message.channel.send(get_price_Yahoo(tmp[1],'.TW','TWD'))

#----------買賣交易----------

    #買入
    elif message.content.startswith('B') or message.content.startswith('b') or message.content.startswith('買'):
        tmp = message.content.split(' ')

        await message.channel.send(active('買入',tmp[1],tmp[2],tmp[3]))

    #賣出
    elif message.content.startswith('S') or message.content.startswith('s') or message.content.startswith('賣'):
        tmp = message.content.split(' ')

        await message.channel.send(active('賣出',tmp[1],tmp[2],tmp[3]))

#----------子函式----------

#交易所套利
def arbitrage(currency,symbol,html_BITO,html_MAX):
    data_BITO = html_BITO.json()
    data_MAX = html_MAX.json()
    price_BITO = data_BITO['data']['lastPrice']
    price_MAX = data_MAX['last']

    per = (float(price_BITO)/float(price_MAX)-1)*100
    money = int(120/(per/100))

    return (str(symbol).upper()+' 對 '+str(currency).upper()+' 交易對的價差(Bito pro/Max)為 '+str(round(per,3))+' % ,最小投資金額為 $ '+str(money)+' '+str(currency).upper())

#BITO 查詢價格
def get_price_BITO(symbol,currency):
    url1 = 'https://api.bitopro.com/v3/tickers/'
    html = requests.get(url1+str(symbol)+'_'+str(currency))

    if html.status_code !=200:
        return ('找不到 '+str(symbol).upper()) 
    else:
        data = html.json()
        price = data['data']['lastPrice']
        return (str(symbol).upper()+' 當前價格為 '+str(price)+' '+str(currency).upper())

#MAX 查詢價格
def get_price_MAX(symbol,currency):
    url1 = 'https://max-api.maicoin.com/api/v2/tickers/'
    html = requests.get(url1+str(symbol)+str(currency))

    if html.status_code !=200:
        return ('找不到 '+str(symbol).upper()) 
    else:
        data = html.json()
        price = data['last']
        return (str(symbol).upper()+' 當前價格為 '+str(price)+' '+str(currency).upper())

#yahoo finance 查詢價格
def get_price_Yahoo(symbol,tp,currency):
    url1 = 'https://query1.finance.yahoo.com/v8/finance/chart/'
    url2 = '?region=US&lang=en-US&includePrePost=false&interval=2m&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'
    headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    html = requests.get(url1+str(symbol)+tp+url2, headers= headers)
    
    if html.status_code !=200:
        return ('找不到 '+str(symbol).upper()) 
    else:
        data = html.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        
        return (str(symbol).upper()+' 當前價格為 '+str(price)+' '+str(currency).upper())

#買賣交易記錄
def active(act,symbol,vol,price):
    return ('在 $ '+str(price)+' '+str(act)+' '+str(vol)+' 枚 '+str(symbol).upper())

client.run('') 