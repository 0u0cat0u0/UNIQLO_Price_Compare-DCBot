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


client.run('') 
