import logging
import telegram
from telegram.ext import CommandHandler, Updater
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns
import random
import requests
import time


class Bot(telegram.Bot):
    def __init__(self, config, *args, **kwargs):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.config = config
        super(Bot, self).__init__(self.config['Bot']['TOKEN'], *args, **kwargs)

        self.btc_price = 0
        self.price = 0
        self.price_cached_at = 0
        self.volume = 0

        self.dwh_deals = {}
        self.dwh_deals_cached_at = 0
        self.df = {}

    def predict(self, bot, update):
        old_price = self.price
        price = self.__get_price()
        increase = price - old_price

        if increase > 10:
            foo = ['moon', 'moon', 'moon', 'moon', 'moon', 'two weeks', 'two weeks', 'ded']
        elif increase > 5:
            foo = ['moon', 'two weeks', 'ded']
        else:
            foo = ['moon', 'ded', 'ded', 'ded', 'ded', 'ded', 'scam', 'ded scam', 'ded scam village', 'delisted']

        bot.send_message(chat_id=update.message.chat_id, text=random.choice(foo))

    def version(self, bot, update):
        message = "Ver 0.3.2"
        bot.send_message(chat_id=update.message.chat_id, text=message)

    def DICS(selfself, bot, update):
        import pywaves as pw

        DICS = "Fweiconow1LnWTwCKdQzqUsbbc6xEnp1tMvFMqpm4e6F"
        myToken = pw.Asset(DICS)
        PAIR = pw.AssetPair(myToken, pw.BTC)
        NODE = "http://nodes.wavesnodes.com"
        # select the network: testnet or mainnet
        NETWORK = "mainnet"
        MATCHER = "http://matcher.wavesnodes.com"
        pw.setNode(NODE, NETWORK)
        pw.setMatcher(MATCHER)
        out = PAIR.orderbook()
        divider = 100000000

        response = "Deal Index Coin for SONM (DICS)  https://bit.ly/2QXKCDF"
        response = response + "\n"
        response = response + "DICS price: " + str(int(out['bids'][0]['price'] / divider)) + " sats"
        response = response + "\n"
        response = response + "DICS/BTC exchange:  https://bit.ly/2Kg7jjZ"

        bot.send_message(chat_id=update.message.chat_id, text=response)

    def data_update(self):
        command = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/ -d"
        command = command + " '"
        command = command + '{"status":1}'
        command = command + "' > livedeal.txt"

        os.system(command)

        f = open('livedeal.txt', 'r')
        k = f.readlines()
        r = k[0].split(',')
        headposition = []
        i = 0
        for item in r:
            if 'deal' in item:
                headposition.append(i)
            i = i + 1
        headposition.append(len(r))
        testlist = []
        for i in range(len(headposition)):
            if headposition[i] > 0:
                # print(headposition[i-1], headposition[i])
                # print(r[headposition[i-1] : headposition[i]])
                testlist.append(r[headposition[i - 1]: headposition[i]])

        self.df = pd.DataFrame(testlist)

        f.close()
        del k
        del r
        del testlist
        del headposition
        del command

        self.df['consumer_ID'] = self.df[18].apply(self.Supplier_ID_conversion)
        self.df['supplier_ID'] = self.df[17].apply(self.Supplier_ID_conversion)
        self.df['price_USD/h'] = self.df[22].apply(self.Price_conversion)
        self.df['Ethash'] = self.df[10].apply(self.Ethash_conversion)
        self.df['master_ID'] = self.df[19].apply(self.Master_ID_conversion)
        self.df['benchmark'] = self.df[1].apply(self.benchmark)

        return self.df

    def stats(self, bot, update):
        self.df = self.data_update()

        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash'] = df11['count'] * df11['mean']
        df12 = df11[['supplier_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df12.to_csv('ethash.csv', index=False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is ' + str(df13['total_Ethash'].sum()) + ' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] * 24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        # print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash'] = df21['count'] * df21['mean']
        # df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df22.to_csv('masterethash.csv', index=False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] * 24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash'] = df11['mean'] * df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] * 24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h', ascending=False)
        # df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending=False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash, df12['price_USD/h'])
        # print("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        # self.df['benchmark'] = self.df[1].apply(benchmark)
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']
        # df_cpu2 = df_cpu[['price_USD/h','master_ID','benchmark',0]].sort_values('price_USD/h', ascending = False)
        #
        # send stats to telegram
        message = ('Real-time total Ethash rate of the entire SONM platform is ' + str(
            df13['total_Ethash'].sum()) + ' Mh/s.')
        message = message + "\n"
        message = message + ('At this moment, total ' + str(
            "{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day are spent on the entire SONM platform.')
        message = message + "\n"
        message = message + ('GPU-Connor currently has ' + str(len(df12)) + ' deals.')
        message = message + "\n"
        message = message + (
                    'GPU-Connor currently pays ' + str("{:.2f}".format(df12['price_USD/h'].sum() * 24)) + " USD/day.")
        message = message + "\n"
        message = message + ('GPU-Connor currently mines ETH with ' + str(df12['Ethash'].sum()) + ' Mh/s hashrate.')
        message = message + "\n"
        message = message + ('There are ' + str(len(df23)) + ' unique suppliers at this moment.')
        message = message + "\n"
        message = message + (
                    'There are ' + str(len(df23[df23['total_Ethash'] > 0])) + ' unique GPU suppliers at this moment.')
        message = message + "\n"
        message = message + ('There are ' + str(
            len(df23) - len(df23[df23['total_Ethash'] > 0])) + ' unique CPU suppliers at this moment.')
        message = message + "\n"
        message = message + ('There are ' + str(len(df11)) + ' unique consumers at this moment.')
        message = message + "\n"
        message = message + ('Currenlty, there are total ' + str(len(self.df)) + ' deals.')
        message = message + "\n"
        message = message + ('Of which ' + str(len(self.df[self.df.Ethash > 0])) + ' deals contain GPU.')
        message = message + "\n"
        message = message + ('And ' + str(len(self.df[self.df.Ethash == 0])) + ' deals are CPU only.')
        message = message + "\n"
        # message = message + ("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        # message = message + "\n"
        message = message + ('CPU-Connor currently has ' + str(len(df_cpu)) + ' deals.')
        message = message + "\n"
        message = message + (
                    'CPU-Connor currently pays ' + str("{:.2f}".format(df_cpu['price_USD/h'].sum() * 24)) + " USD/day.")
        bot.send_message(chat_id=update.message.chat_id, text=message)
        #
        #
        del df10
        del df11
        del df12
        del df13
        del df20
        del df21
        del df22
        del df23
        del df_cpu

    def gpu(self, bot, update):
        self.df = self.data_update()

        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash'] = df11['count'] * df11['mean']
        df12 = df11[['supplier_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df12.to_csv('ethash.csv', index=False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is ' + str(
            df13['total_Ethash'].sum()) + ' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] * 24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        # print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash'] = df21['count'] * df21['mean']
        # df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df22.to_csv('masterethash.csv', index=False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] * 24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)

        message = 'GPU suppliers: ' + str(len(df23[df23['total_Ethash'] > 0]))
        message = message + "\n"
        message = message + 'GPU deals: ' + str(len(self.df[self.df.Ethash > 0]))
        message = message + "\n"

        bot.send_message(chat_id=update.message.chat_id, text=message)

        del df23
        del df22
        del df21
        del df20
        del df13
        del df12
        del df11
        del df10

    def consumers(self, bot, update):
        self.df = self.data_update()

        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash'] = df11['count'] * df11['mean']
        df12 = df11[['supplier_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df12.to_csv('ethash.csv', index=False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is ' + str(df13['total_Ethash'].sum()) + ' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] * 24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        # print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash'] = df21['count'] * df21['mean']
        # df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df22.to_csv('masterethash.csv', index=False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] * 24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash'] = df11['mean'] * df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] * 24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h', ascending=False)
        # df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending=False)

        #    Consumer plot
        sns.set()
        sns.lmplot(y="total_Ethash", x="total_expense_USD/h", data=df11, fit_reg=False, hue='consumer_ID',
                   legend=True).savefig("consumer.png")
        bot.send_photo(chat_id=update.message.chat_id, photo=open('consumer.png', 'rb'))

        del df11
        del df10
        del df12
        del df13
        del df20
        del df21
        del df22
        del df23

    def suppliers(self, bot, update):
        self.df = self.data_update()

        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash'] = df11['count'] * df11['mean']
        df12 = df11[['supplier_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df12.to_csv('ethash.csv', index=False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is ' + str(df13['total_Ethash'].sum()) + ' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] * 24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        # print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash'] = df21['count'] * df21['mean']
        # df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df22.to_csv('masterethash.csv', index=False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] * 24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash'] = df11['mean'] * df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] * 24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h',
                                ascending=False)  # df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending=False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash, df12['price_USD/h'])
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']

        # Supplier plot
        sns.set()
        sns.lmplot(y="total_Ethash", x="total_revenue_USD/h", data=df23, fit_reg=False, hue='master_ID',
                   legend=True).savefig("supplier.png")
        #
        bot.send_photo(chat_id=update.message.chat_id, photo=open('supplier.png', 'rb'))

        del df22
        del df23
        del df21
        del df20
        del df13
        del df12
        del df10
        del df11
        del df_cpu

    def profit(self, bot, update):
        self.df = self.data_update()

        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash'] = df11['count'] * df11['mean']
        df12 = df11[['supplier_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df12.to_csv('ethash.csv', index=False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is ' + str(df13['total_Ethash'].sum()) + ' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] * 24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        # print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash'] = df21['count'] * df21['mean']
        # df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID', 'total_Ethash', 'count']].sort_values('total_Ethash', ascending=False)
        df22.to_csv('masterethash.csv', index=False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] * 24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash'] = df11['mean'] * df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] * 24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h', ascending=False)
        # df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending=False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash, df12['price_USD/h'])
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']

        # Profitability
        msg = ("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        msg = msg + "\n"
        msg = msg + (" ")
        msg = msg + "\n"
        msg = msg + ("GPU card                EThash     SONM profitability")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1050 TI       15 Mh/s    " + str("{:.2f}".format(slope * 15 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1060          24 Mh/s    " + str("{:.2f}".format(slope * 24 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1070 TI       32 Mh/s    " + str("{:.2f}".format(slope * 32 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1080          27 Mh/s    " + str("{:.2f}".format(slope * 27 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1080 TI       37 Mh/s    " + str("{:.2f}".format(slope * 37 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX TITAN         40 Mh/s    " + str("{:.2f}".format(slope * 40 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1080 +pill    40 Mh/s    " + str("{:.2f}".format(slope * 40 * 24)) + " USD/day")
        msg = msg + "\n"
        msg = msg + ("Nvida GTX 1080 TI +pill 50 Mh/s    " + str("{:.2f}".format(slope * 50 * 24)) + " USD/day")
        # 
        bot.send_message(chat_id=update.message.chat_id, text=msg)

        del df11
        del df_cpu
        del df10
        del df12
        del df13
        del df20
        del df21
        del df23
        del df22

    def benchmark(self, content):
        return int(content[content.find('[') + 1:])

    def Supplier_ID_conversion(self, content):
        return content[14:-1]

    def Price_conversion(self, content):
        unit = 10.0 ** 18.0
        if 'price' in content:
            return float(content[9:-1]) / unit * 60 * 60
        if 'duration' in content:
            return float(content[11:-1]) / unit * 60 * 60

    def Ethash_conversion(self, content):
        return float(content) / 1000000

    def Master_ID_conversion(self, content):
        return content[12:-1]

    def total_revenue(self, address):
        return self.df[self.df.supplier_ID == address]['price_USD/h'].sum()

    def total_master_revenue(self, address):
        return self.df[self.df.master_ID == address]['price_USD/h'].sum()

    def total_expense(self, address):
        return self.df[self.df.consumer_ID == address]['price_USD/h'].sum()

    def token_price(self, bot, update):
        old_price = self.price
        price = self.__get_price()

        usd_price = format((self.btc_price * price/100000000), '.3f')

        msg = """\
SNM Price: {price} sats (${usd} US)\n\
Volume: {vol} BTC\n\
\n\
(Source: Binance)""".format(price=price, usd=usd_price, vol=self.volume)

        bot.send_message(chat_id=update.message.chat_id, text=msg)

    def __commands(self, dispatcher):
        dispatcher.add_handler(CommandHandler("stats", self.stats))
        dispatcher.add_handler(CommandHandler("version", self.version))
        dispatcher.add_handler(CommandHandler("profit", self.profit))
        dispatcher.add_handler(CommandHandler("suppliers", self.suppliers))
        dispatcher.add_handler(CommandHandler("consumers", self.consumers))
        dispatcher.add_handler(CommandHandler("predict", self.predict))
        dispatcher.add_handler(CommandHandler("price", self.token_price))
        dispatcher.add_handler(CommandHandler("gpu", self.gpu))
        dispatcher.add_handler(CommandHandler("DICS", self.DICS))

    def __get_dwh_deals(self):
        ts = time.time()
        if ts > self.deals_cached_at + 60:
            try:
                r = requests.request(method='get', url='https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/', data='{"status": 1}')
                data = r.json()
                self.deals = data
                self.deals_cached_at = ts
            except Exception as e:
                print(e)
                return self.deals  # return latest known price

        return self.deals

    def __get_price(self):
        ts = time.time()
        if ts > self.price_cached_at + 60:
            try:
                r = requests.get('https://api.binance.com/api/v1/ticker/24hr?symbol=BTCUSDT')
                self.btc_price = int(float(r.json()["lastPrice"]))
                r = requests.get('https://api.binance.com/api/v1/ticker/24hr?symbol=SNMBTC')
                data = r.json()
                self.price = int(float(data["lastPrice"]) * 100000000)  # convert to satoshis
                self.volume = int(float(data["quoteVolume"]))
                self.price_cached_at = ts
            except Exception as e:
                print(e)
                return self.price  # return latest known price

        return self.price

    def start(self):
        updater = Updater(token=self.config['Bot']['TOKEN'])
        dispatcher = updater.dispatcher

        self.__commands(dispatcher)

        updater.start_polling()
        updater.idle()
