import logging
import telegram
from telegram.ext import CommandHandler, Updater
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns


class Bot(telegram.Bot):
    def __init__(self, config, *args, **kwargs):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.config = config
        super(Bot,self).__init__(self.config['Bot']['TOKEN'], *args, **kwargs)
         
        self.df = pd.DataFrame()	

    def hello(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text ='Hello World')

    def stats(self, bot, update):
        command = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/ -d" 
        command = command + " '" 
        command = command + '{"status":1}'
        command = command +"' > livedeal.txt"
        os.system(command)
        #
        f = open('livedeal.txt','r')
        #
        k = f.readlines()
        r = k[0].split(',')
        headposition = []
        i = 0
        for item in r:
            if 'deal' in item:
                headposition.append(i)
            i = i+1
        #
        testlist = []
        for i in range(len(headposition)):
            if headposition[i]>0:
                #print(headposition[i-1], headposition[i])
                #print(r[headposition[i-1] : headposition[i]])
                testlist.append(r[headposition[i-1] : headposition[i]])
        #
        self.df = pd.DataFrame(testlist)
        #
        #Data Cleaning
        self.df['consumer_ID'] = self.df[15].apply(self.Supplier_ID_conversion)
        self.df['supplier_ID'] = self.df[14].apply(self.Supplier_ID_conversion)
        self.df['price_USD/h'] = self.df[19].apply(self.Price_conversion)
        self.df['Ethash'] = self.df[10].apply(self.Ethash_conversion)
        self.df['master_ID'] =  self.df[16].apply(self.Master_ID_conversion)
        self.df['benchmark'] = self.df[1].apply(self.benchmark)
        unit = 10.0**18.0
        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash']= df11['count']*df11['mean']
        df12 = df11[['supplier_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df12.to_csv('ethash.csv', index = False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] *24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        #print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash']= df21['count']*df21['mean']
#df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df22.to_csv('masterethash.csv', index = False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] *24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash']= df11['mean']*df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] *24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h',ascending=False)
	#df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending = False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash,df12['price_USD/h'])
        #print("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        #self.df['benchmark'] = self.df[1].apply(benchmark)
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']
        #df_cpu2 = df_cpu[['price_USD/h','master_ID','benchmark',0]].sort_values('price_USD/h', ascending = False)
        #
        #send stats to telegram
        message = ('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s.')
        message = message + "\n"
        message = message + ('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day are spent on the entire SONM platform.')
        message = message + "\n"
        message = message + ('GPU-Connor currently has '+ str(len(df12)) + ' deals.')
        message = message + "\n"
        message = message + ('GPU-Connor currently pays ' + str("{:.2f}".format(df12['price_USD/h'].sum()*24)) + " USD/day.") 
        message = message + "\n"
        message = message + ('GPU-Connor currently mines ETH with ' + str(df12['Ethash'].sum()) + ' Mh/s hashrate.')
        message = message + "\n"
        message = message + ('There are '+ str(len(df23))+ ' unique suppliers at this moment.')
        message = message + "\n"
        message = message + ('There are ' + str(len(df23[df23['total_Ethash']>0])) + ' unique GPU sppliers at this moment.')
        message = message + "\n"
        message = message + ('There are ' + str(len(df23)-len(df23[df23['total_Ethash']>0])) + ' unique CPU sppliers at this moment.')
        message = message + "\n"
        message = message + ('There are '+ str(len(df11))+ ' unique consumers at this moment.')
        message = message + "\n"
        message = message +('Currenlty, there are total '+ str(len(self.df)) + ' deals.')
        message = message + "\n"
        message = message + ('Of which ' + str(len(self.df[self.df.Ethash>0])) + ' deals contain GPU.')
        message = message + "\n"
        message = message +('And ' + str(len(self.df[self.df.Ethash==0])) + ' deals are CPU only.')
        message = message + "\n"
        #message = message + ("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        #message = message + "\n"
        message = message + ('CPU-Connor currently has '+ str(len(df_cpu)) + ' deals.')
        message = message + "\n"
        message = message + ('CPU-Connor currently pays ' + str("{:.2f}".format(df_cpu['price_USD/h'].sum()*24)) + " USD/day.")
        bot.send_message(chat_id=update.message.chat_id, text =message)
        #
        #


    def consumers(self, bot, update):
        command = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/ -d" 
        command = command + " '" 
        command = command + '{"status":1}'
        command = command +"' > livedeal.txt"
        os.system(command)
        #
        f = open('livedeal.txt','r')
        #$
        k = f.readlines()
        r = k[0].split(',')
        headposition = []
        i = 0
        for item in r:
            if 'deal' in item:
                headposition.append(i)
            i = i+1
        #
        testlist = []
        for i in range(len(headposition)):
            if headposition[i]>0:
                #print(headposition[i-1], headposition[i])
          	#print(r[headposition[i-1] : headposition[i]])
                testlist.append(r[headposition[i-1] : headposition[i]])
        #
        self.df = pd.DataFrame(testlist)
        #
        #Data Cleaning
        self.df['consumer_ID'] = self.df[15].apply(self.Supplier_ID_conversion)
        self.df['supplier_ID'] = self.df[14].apply(self.Supplier_ID_conversion)
        self.df['price_USD/h'] = self.df[19].apply(self.Price_conversion)
        self.df['Ethash'] = self.df[10].apply(self.Ethash_conversion)
        self.df['master_ID'] =  self.df[16].apply(self.Master_ID_conversion)
        self.df['benchmark'] = self.df[1].apply(self.benchmark)
        unit = 10.0**18.0
        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash']= df11['count']*df11['mean']
        df12 = df11[['supplier_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df12.to_csv('ethash.csv', index = False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] *24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        #print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash']= df21['count']*df21['mean']
#df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df22.to_csv('masterethash.csv', index = False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] *24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash']= df11['mean']*df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] *24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h',ascending=False)
	#df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending = False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash,df12['price_USD/h'])
        #print("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        #self.df['benchmark'] = self.df[1].apply(benchmark)
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']
        #df_cpu2 = df_cpu[['price_USD/h','master_ID','benchmark',0]].sort_values('price_USD/h', ascending = False)
          
        
        #    Consumer plot
        sns.set()
        sns.lmplot( y="total_Ethash", x="total_expense_USD/h", data=df11, fit_reg=False, hue='consumer_ID', legend=True).savefig("consumer.png")
        bot.send_photo(chat_id=update.message.chat_id, photo=open('consumer.png', 'rb'))
        


        # Supplier plot
        #sns.set()
        #sns.lmplot( y="total_Ethash", x="total_revenue_USD/h", data=df23, fit_reg=False, hue='master_ID', legend=True).savefig("supplier.png")
        #
        #bot.send_photo(chat_id=update.message.chat_id, photo=open('supplier.png', 'rb'))
       
       
      
     
    
   
  
 














    def suppliers(self, bot, update):
        command = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/ -d" 
        command = command + " '" 
        command = command + '{"status":1}'
        command = command +"' > livedeal.txt"
        os.system(command)
        #
        f = open('livedeal.txt','r')
        #$
        k = f.readlines()
        r = k[0].split(',')
        headposition = []
        i = 0
        for item in r:
            if 'deal' in item:
                headposition.append(i)
            i = i+1
        #
        testlist = []
        for i in range(len(headposition)):
            if headposition[i]>0:
                #print(headposition[i-1], headposition[i])
          	#print(r[headposition[i-1] : headposition[i]])
                testlist.append(r[headposition[i-1] : headposition[i]])
        #
        self.df = pd.DataFrame(testlist)
        #
        #Data Cleaning
        self.df['consumer_ID'] = self.df[15].apply(self.Supplier_ID_conversion)
        self.df['supplier_ID'] = self.df[14].apply(self.Supplier_ID_conversion)
        self.df['price_USD/h'] = self.df[19].apply(self.Price_conversion)
        self.df['Ethash'] = self.df[10].apply(self.Ethash_conversion)
        self.df['master_ID'] =  self.df[16].apply(self.Master_ID_conversion)
        self.df['benchmark'] = self.df[1].apply(self.benchmark)
        unit = 10.0**18.0
        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash']= df11['count']*df11['mean']
        df12 = df11[['supplier_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df12.to_csv('ethash.csv', index = False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] *24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        #print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash']= df21['count']*df21['mean']
#df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df22.to_csv('masterethash.csv', index = False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] *24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash']= df11['mean']*df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] *24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h',ascending=False)
	#df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending = False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash,df12['price_USD/h'])
        #print("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        #self.df['benchmark'] = self.df[1].apply(benchmark)
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']
        #df_cpu2 = df_cpu[['price_USD/h','master_ID','benchmark',0]].sort_values('price_USD/h', ascending = False)
          


        # Supplier plot
        sns.set()
        sns.lmplot( y="total_Ethash", x="total_revenue_USD/h", data=df23, fit_reg=False, hue='master_ID', legend=True).savefig("supplier.png")
        #
        bot.send_photo(chat_id=update.message.chat_id, photo=open('supplier.png', 'rb'))
       



    def profit(self, bot, update):
        command = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/ -d" 
        command = command + " '" 
        command = command + '{"status":1}'
        command = command +"' > livedeal.txt"
        os.system(command)
        #
        f = open('livedeal.txt','r')
        #$
        k = f.readlines()
        r = k[0].split(',')
        headposition = []
        i = 0
        for item in r:
            if 'deal' in item:
                headposition.append(i)
            i = i+1
        #
        testlist = []
        for i in range(len(headposition)):
            if headposition[i]>0:
                #print(headposition[i-1], headposition[i])
          	#print(r[headposition[i-1] : headposition[i]])
                testlist.append(r[headposition[i-1] : headposition[i]])
        #
        self.df = pd.DataFrame(testlist)
        #
        #Data Cleaning
        self.df['consumer_ID'] = self.df[15].apply(self.Supplier_ID_conversion)
        self.df['supplier_ID'] = self.df[14].apply(self.Supplier_ID_conversion)
        self.df['price_USD/h'] = self.df[19].apply(self.Price_conversion)
        self.df['Ethash'] = self.df[10].apply(self.Ethash_conversion)
        self.df['master_ID'] =  self.df[16].apply(self.Master_ID_conversion)
        self.df['benchmark'] = self.df[1].apply(self.benchmark)
        unit = 10.0**18.0
        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash']= df11['count']*df11['mean']
        df12 = df11[['supplier_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df12.to_csv('ethash.csv', index = False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] *24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        #print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash']= df21['count']*df21['mean']
#df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df22.to_csv('masterethash.csv', index = False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] *24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash']= df11['mean']*df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] *24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h',ascending=False)
	#df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending = False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash,df12['price_USD/h'])
        #print("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        #self.df['benchmark'] = self.df[1].apply(benchmark)
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']

     


       
        # Profitability
        msg = ("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        msg = msg+"\n"
        msg = msg+(" ")
        msg = msg+"\n"
        msg = msg +("GPU card                EThash     SONM profitability")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1050 TI       15 Mh/s    " + str("{:.2f}".format(slope*15*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1060          24 Mh/s    " + str("{:.2f}".format(slope*24*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1070 TI       32 Mh/s    " + str("{:.2f}".format(slope*32*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1080          27 Mh/s    " + str("{:.2f}".format(slope*27*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1080 TI       37 Mh/s    " + str("{:.2f}".format(slope*37*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg+("Nvida GTX TITAN         40 Mh/s    " + str("{:.2f}".format(slope*40*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg+("Nvida GTX 1080 +pill    40 Mh/s    " + str("{:.2f}".format(slope*40*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg+("Nvida GTX 1080 TI +pill 50 Mh/s    " + str("{:.2f}".format(slope*50*24))+ " USD/day")
        # 
        bot.send_message(chat_id=update.message.chat_id, text =msg)
        



    def test(self, bot, update):
        command = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetDeals/ -d" 
        command = command + " '" 
        command = command + '{"status":1}'
        command = command +"' > livedeal.txt"
        os.system(command)
        #
        f = open('livedeal.txt','r')
        #$
        k = f.readlines()
        r = k[0].split(',')
        headposition = []
        i = 0
        for item in r:
            if 'deal' in item:
                headposition.append(i)
            i = i+1
        #
        testlist = []
        for i in range(len(headposition)):
            if headposition[i]>0:
                #print(headposition[i-1], headposition[i])
                #print(r[headposition[i-1] : headposition[i]])
                testlist.append(r[headposition[i-1] : headposition[i]])
        #
        self.df = pd.DataFrame(testlist)
        #
        #Data Cleaning
        self.df['consumer_ID'] = self.df[15].apply(self.Supplier_ID_conversion)
        self.df['supplier_ID'] = self.df[14].apply(self.Supplier_ID_conversion)
        self.df['price_USD/h'] = self.df[19].apply(self.Price_conversion)
        self.df['Ethash'] = self.df[10].apply(self.Ethash_conversion)
        self.df['master_ID'] =  self.df[16].apply(self.Master_ID_conversion)
        self.df['benchmark'] = self.df[1].apply(self.benchmark)
        unit = 10.0**18.0
        # Run stats
        df10 = self.df.groupby('supplier_ID').describe()['Ethash']
        df10.to_csv('eth.csv')
        df11 = pd.read_csv('eth.csv')
        df11['total_Ethash']= df11['count']*df11['mean']
        df12 = df11[['supplier_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df12.to_csv('ethash.csv', index = False)
        df13 = pd.read_csv('ethash.csv')
        print('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s')
        df13['total_revenue_USD/h'] = df13['supplier_ID'].apply(self.total_revenue)
        df13['total_revenue_USD/d'] = df13['total_revenue_USD/h'] *24
        df13['revenue_USD/d'] = df13['total_revenue_USD/d'].map('${:,.2f}'.format)
        #print('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day is spent on the entire SONM platform.')
        df20 = self.df.groupby('master_ID').describe()['Ethash']
        df20.to_csv('mastereth.csv')
        df21 = pd.read_csv('mastereth.csv')
        df21['total_Ethash']= df21['count']*df21['mean']
#df21[['master_ID','total_Ethash','count']]
        df22 = df21[['master_ID','total_Ethash','count']].sort_values('total_Ethash', ascending = False)
        df22.to_csv('masterethash.csv', index = False)
        df23 = pd.read_csv('masterethash.csv')
        df23['total_revenue_USD/h'] = df23['master_ID'].apply(self.total_master_revenue)
        df23['total_revenue_USD/d'] = df23['total_revenue_USD/h'] *24
        df23['revenue_USD/d'] = df23['total_revenue_USD/d'].map('${:,.2f}'.format)
        df10 = self.df.groupby('consumer_ID').describe()['Ethash']
        df10.to_csv('consumer.csv')
        df11 = pd.read_csv('consumer.csv')
        df11['total_Ethash']= df11['mean']*df11['count']
        df11['total_expense_USD/h'] = df11['consumer_ID'].apply(self.total_expense)
        df11['total_expense_USD/d'] = df11['total_expense_USD/h'] *24
        df11['expense_USD/d'] = df11['total_expense_USD/d'].map('${:,.2f}'.format)
        df11 = df11.sort_values('total_expense_USD/h',ascending=False)
	#df[df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = self.df[self.df.consumer_ID == '0x417c92FbD944b125A578848DE44a4FD9132E0911']
        df12 = df12.sort_values(['Ethash', 'price_USD/h'], ascending = False)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df12.Ethash,df12['price_USD/h'])
        #print("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        #self.df['benchmark'] = self.df[1].apply(benchmark)
        df_cpu = self.df[self.df.consumer_ID == '0x4C5BAf6Fa57AA4b37DB3dAcd5eAf5A220Db638c7']
        #df_cpu2 = df_cpu[['price_USD/h','master_ID','benchmark',0]].sort_values('price_USD/h', ascending = False)
        #
        #send stats to telegram
        message = ('Real-time total Ethash rate of the entire SONM platform is '+ str(df13['total_Ethash'].sum()) +' Mh/s.')
        message = message + "\n"
        message = message + ('At this moment, total ' + str("{:.2f}".format(df13['total_revenue_USD/d'].sum())) + ' USD/day are spent on the entire SONM platform.')
        message = message + "\n"
        message = message + ('GPU-Connor currently has '+ str(len(df12)) + ' deals.')
        message = message + "\n"
        message = message + ('GPU-Connor currently pays ' + str("{:.2f}".format(df12['price_USD/h'].sum()*24)) + " USD/day.") 
        message = message + "\n"
        message = message + ('GPU-Connor currently mines ETH with ' + str(df12['Ethash'].sum()) + ' Mh/s hashrate.')
        message = message + "\n"
        message = message + ('There are '+ str(len(df23))+ ' unique suppliers at this moment.')
        message = message + "\n"
        message = message + ('There are ' + str(len(df23[df23['total_Ethash']>0])) + ' unique GPU sppliers at this moment.')
        message = message + "\n"
        message = message + ('There are ' + str(len(df23)-len(df23[df23['total_Ethash']>0])) + ' unique CPU sppliers at this moment.')
        message = message + "\n"
        message = message + ('There are '+ str(len(df11))+ ' unique consumers at this moment.')
        message = message + "\n"
        message = message +('Currenlty, there are total '+ str(len(self.df)) + ' deals.')
        message = message + "\n"
        message = message + ('Of which ' + str(len(self.df[self.df.Ethash>0])) + ' deals contain GPU.')
        message = message + "\n"
        message = message +('And ' + str(len(self.df[self.df.Ethash==0])) + ' deals are CPU only.')
        message = message + "\n"
        message = message + ("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        message = message + "\n"
        message = message + ('CPU-Connor currently has '+ str(len(df_cpu)) + ' deals.')
        message = message + "\n"
        message = message + ('CPU-Connor currently pays ' + str("{:.2f}".format(df_cpu['price_USD/h'].sum()*24)) + " USD/day.")
        #
        #
        bot.send_message(chat_id=update.message.chat_id, text =message)
        
        #Consumer plot
        sns.set()
        sns.lmplot( y="total_Ethash", x="total_expense_USD/h", data=df11, fit_reg=False, hue='consumer_ID', legend=True).savefig("consumer.png")
        #bot.send_message(chat_id=update.message.chat_id, text =message)
        bot.send_photo(chat_id=update.message.chat_id, photo=open('consumer.png', 'rb'))
        


        # Supplier plot
        sns.set()
        sns.lmplot( y="total_Ethash", x="total_revenue_USD/h", data=df23, fit_reg=False, hue='master_ID', legend=True).savefig("supplier.png")
        #
        bot.send_photo(chat_id=update.message.chat_id, photo=open('supplier.png', 'rb'))
       
        # Profitability
        msg = ("Current profitability (USD/h) = " + str(slope) + " * Ethash(Mh/s)")
        msg = msg+"\n"
        msg = msg+(" ")
        msg = msg+"\n"
        msg = msg +("GPU card                EThash     SONM profitability")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1050 TI       15 Mh/s    " + str("{:.2f}".format(slope*15*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1060          24 Mh/s    " + str("{:.2f}".format(slope*24*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1070 TI       32 Mh/s    " + str("{:.2f}".format(slope*32*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1080          27 Mh/s    " + str("{:.2f}".format(slope*27*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg +("Nvida GTX 1080 TI       37 Mh/s    " + str("{:.2f}".format(slope*37*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg+("Nvida GTX TITAN         40 Mh/s    " + str("{:.2f}".format(slope*40*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg+("Nvida GTX 1080 +pill    40 Mh/s    " + str("{:.2f}".format(slope*40*24))+ " USD/day")
        msg = msg+"\n"
        msg = msg+("Nvida GTX 1080 TI +pill 50 Mh/s    " + str("{:.2f}".format(slope*50*24))+ " USD/day")
        # 
        bot.send_message(chat_id=update.message.chat_id, text =msg)
        






    def benchmark(self,content):
        return int(content[content.find('[')+1:])

    def Supplier_ID_conversion(self,content):
        return content[14:-1]

    def Price_conversion(self, content):
        unit = 10.0**18.0
        if 'price' in content:
            return float(content[9:-1])/unit * 60 *60
        if 'duration' in content:
            return float(content[11:-1])/unit * 60 * 60

    def Ethash_conversion(self, content):
        return float(content)/1000000


    def Master_ID_conversion(self, content):
        return content[12:-1]

    def total_revenue(self, address):
        return self.df[self.df.supplier_ID == address]['price_USD/h'].sum()

    def total_master_revenue(self, address):
        return self.df[self.df.master_ID == address]['price_USD/h'].sum()

    def total_expense(self, address):
        return self.df[self.df.consumer_ID == address]['price_USD/h'].sum()




    def __commands(self, dispatcher):
        # /start => respond_start()
        start_handler = CommandHandler('start', self.respond_start)
        dispatcher.add_handler(start_handler)

    def start(self):
        updater = Updater(token=self.config['Bot']['TOKEN'])
        dispatcher = updater.dispatcher

        self.__commands(dispatcher)

        dispatcher.add_handler(CommandHandler("stats", self.stats))
        dispatcher.add_handler(CommandHandler("hello", self.hello))
        dispatcher.add_handler(CommandHandler("test", self.test))
        dispatcher.add_handler(CommandHandler("profit", self.profit))
        dispatcher.add_handler(CommandHandler("suppliers", self.suppliers))
        dispatcher.add_handler(CommandHandler("consumers", self.consumers))


       
        updater.start_polling()
        updater.idle()

    def respond_start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="test")
