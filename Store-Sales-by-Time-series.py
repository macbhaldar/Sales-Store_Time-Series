# import libraries
import numpy as np
import pandas as pd
import zipfile
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from warnings import simplefilter
simplefilter("ignore")

import gc # for garbage cleaning

%config Completer.use_jedi = False

import os
for dirname, _, filenames in os.walk('data'):
    for filename in filenames:
        print(os.path.join(dirname, filename))
        
# import datasets 
oil_data = pd.read_csv("data/oil.csv")
holiday_data = pd.read_csv("data/holidays_events.csv")
store_data = pd.read_csv("data/stores.csv")
transaction_data = pd.read_csv("data/transactions.csv")
sample = pd.read_csv("data/sample_submission.csv")
test_data = pd.read_csv("data/test.csv")
zf = zipfile.ZipFile('data/train.csv.zip')
train_data = pd.read_csv(zf.open("train.csv"))

test_data.head()

sample.head()

train_data.head()

train_data.info()

print('there are {} different product families'.format(train_data.family.nunique()))
print('there are {} different stores'.format(train_data.store_nbr.nunique()))

process_train = train_data.copy()

del train_data

process_train['date'] = pd.to_datetime(process_train['date'])
process_train = process_train.set_index('date')
process_train = process_train.drop('id',axis = 1)
process_train[['store_nbr','family']].astype('category') #to reduce ram usage
process_train

process_train.isna().sum()

def count_day_gap(df):
    temp = df.reset_index().groupby(['date']).sales.sum()
    return (temp.index[1:]-temp.index[:-1]).value_counts()
count_day_gap(process_train)

temp = process_train.reset_index().groupby(['date']).sales.sum().to_frame()
gap = (temp.index[1:]-temp.index[:-1]).to_list()
gap.insert(0,'first day') 
temp['gap'] = gap

day_skip = temp.groupby('gap').get_group(temp.gap.unique()[2])
day_skip

del temp

process_train.groupby('date').sales.sum().sort_values().head(10)

date_fam_sale = process_train.groupby(['date','family']).sum().sales
unstack = date_fam_sale.unstack()
unstack = unstack.resample('1M').sum()

fig, ax = plt.subplots(figsize=(20, 10))
ax.set(title="'Total Monthly Sales From each Family")
plt.stackplot(unstack.index,unstack.T,labels=unstack.T.index)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.axvline(x=pd.Timestamp('2016-04-16'),color='black',linestyle='--',linewidth=5,alpha=0.7)
plt.text(pd.Timestamp('2016-04-20'),30000000,'  The Earthquake',rotation=360,c='black',size=17)
plt.xticks(rotation=90)
plt.legend(loc='lower center',bbox_to_anchor=(0.5,-0.2),ncol=11)
plt.show()

del unstack
del date_fam_sale

month_family = process_train.groupby('family').resample('M').sales.sum()

fig, ax = plt.subplots(figsize=(7,7))
plt.barh(month_family.groupby('family').sum().sort_values().index,month_family.groupby('family').sum().sort_values())
ax.set(title='Total Sales by Product Family')
plt.show()

total_sale = month_family.sum()
family_sale = month_family.groupby('family').sum().sort_values()
proportion = ((family_sale/total_sale)*100).sort_values(ascending=False)
proportion = pd.DataFrame(proportion)
proportion.head()

del family_sale

fig, ax = plt.subplots(figsize=(18, 7))
ax.set(title="'Total Sales Across All Stores")
total_sales = process_train.sales.groupby("date").sum()
plt.plot(total_sales)

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.xticks(rotation=70)
plt.axvline(x=pd.Timestamp('2016-04-16'),color='r',linestyle='--',linewidth=4,alpha=0.3)
plt.text(pd.Timestamp('2016-04-20'),1400000,'The Earthquake',rotation=360,c='r')
plt.show()

daily_sale_dict = {}
for i in process_train.store_nbr.unique():
    daily_sale = process_train[process_train['store_nbr']==i]
    daily_sale_dict[i] = daily_sale
    
fig = plt.figure(figsize=(30,30))
for i in daily_sale_dict.keys():
    plt.subplot(8,7,i)
    plt.title('Store {} sale'.format(i))
    plt.tight_layout(pad=5)
    sale = daily_sale_dict[i].sales
    sale.plot()
    plt.axvline(x=pd.Timestamp('2016-04-16'),color='r',linestyle='--',linewidth=2,alpha=0.3)
    
by_fam_dic = {}
fam_list = process_train.family.unique()

for fam in fam_list:
    by_fam_dic[fam] = process_train[process_train['family']==fam].sales
    
fig = plt.figure(figsize=(30,50))

for i,fam in enumerate(by_fam_dic.keys()):
    plt.subplot(11,3,i+1)
    plt.title('{} sale'.format(fam))
    plt.tight_layout(pad=5)
    sale = by_fam_dic[fam]
    sale.plot()
    plt.axvline(x=pd.Timestamp('2016-04-16'),color='r',linestyle='--',linewidth=2,alpha=0.3)
    
del by_fam_dic
del fam_list
store_data.head(3)

join_df = process_train.merge(store_data,on='store_nbr')
join_df.set_index(process_train.index)
join_df['date'] = process_train.index
join_df = join_df.set_index('date')

join_df.head()

 def show_type_df(join_store_type_df):
    mean_sales_type = join_store_type_df.groupby('type').sales.mean()
    median_sales_type = join_store_type_df.groupby('type').sales.median()
    number=join_store_type_df.groupby('type').store_nbr.nunique()

    type_df = pd.DataFrame((mean_sales_type,median_sales_type,number))
    type_df = type_df.T
    type_df.columns = ['mean','median','number of store']

    return type_df
  
show_type_df(join_df)

def show_cluster_summary(join_store_type_df):
    mean_sales_cluster = join_store_type_df.groupby('cluster').sales.mean()
    median_sales_cluster = join_store_type_df.groupby('cluster').sales.median()
    number=join_store_type_df.groupby('cluster').store_nbr.nunique()

    cluster_df = pd.DataFrame((mean_sales_cluster,median_sales_cluster,number))
    cluster_df = cluster_df.T
    cluster_df.columns = ['mean','median','number of store']

    return cluster_df.sort_values('mean', ascending=False)
  
show_cluster_summary(join_df)

def show_city_df(join_store_type_df):    
    mean_sales_city = join_store_type_df.groupby('city').sales.mean()
    median_sales_city = join_store_type_df.groupby('city').sales.median()
    number=join_store_type_df.groupby('city').store_nbr.nunique()

    city_df = pd.DataFrame((mean_sales_city,median_sales_city,number))
    city_df = city_df.T
    city_df.columns = ['mean','median','number of store']

    return city_df.sort_values('mean', ascending=False)
  
show_city_df(join_df)

del join_df

# Correlation amoung store
import seaborn as sns

a = process_train[["store_nbr", "sales"]]
a["ind"] = 1
a["ind"] = a.groupby("store_nbr").ind.cumsum().values 
a = pd.pivot(a, index = "ind", columns = "store_nbr", values = "sales").corr() 

mask = np.triu(a.corr())

plt.figure(figsize=(20, 20))
sns.heatmap(a,
         annot=True,
         fmt='.1f',
         square=True,
         mask=mask,
         linewidths=1,
         cbar=False)
plt.title("Correlations among stores",fontsize = 24)
plt.show()

gc.collect()

store_20 = process_train.groupby(['store_nbr','date']).sales.sum().loc[20]
store_20.loc['2013-01-01':'2015-01-01']

del store_20

print('Spearman Rank Correlation = {}'.format(
    process_train.sales.corr(process_train.onpromotion,method='spearman')))
    
from datetime import datetime as dt

def show_dow_sales():
    day_group = process_train.reset_index()[['date','sales']]
    day_group = day_group.groupby('date')
    day_group = day_group.sales.mean().to_frame()
    day_group['dow'] = day_group.index.day_of_week
    day_group = day_group.groupby('dow').sum()
    plt.bar(day_group.index,day_group['sales'])
    plt.title('Average sales on day of week')
    plt.show()

def show_month_group_sale():
    month_group = process_train['sales'].to_frame()
    month_group['moy'] = month_group.index.month
    month_group = month_group.groupby('moy').sales.mean().to_frame()
    plt.bar(month_group.index,month_group['sales'])
    plt.title('Average sales on Month of Year')
    plt.show()
    
show_dow_sales()
show_month_group_sale()

holiday_data = pd.read_csv("input/holidays_events.csv",index_col='date',parse_dates=['date'])
holiday_data

holiday_data.locale_name.value_counts().head()

ny_dic = {'type': 'Holiday','locale':'National','locale_name':'Ecuador','description': 'New Year Day','transferred':'False'}
ny_date = pd.to_datetime(['2012-01-01','2013-01-01','2014-01-01','2015-01-01','2016-01-01','2017-01-01','2018-01-01'])

cm_dic = {'type': 'Holiday','locale':'National','locale_name':'Ecuador','description': 'Christmas Day','transferred':'False'}
cm_date = pd.to_datetime(['2012-12-25','2013-12-25','2014-12-25','2015-12-25','2016-12-25','2017-12-25','2018-12-25'])

for date in ny_date:
    holiday_data.loc[date] = ['Holiday','National', 'Ecuador', 'New Year day','False']
    
for date in cm_date:
    holiday_data.loc[date] = ['Holiday','National', 'Ecuador', 'Christmas day','False']
    
holiday_data = holiday_data.sort_index()

calendar = pd.DataFrame(index = pd.date_range('2013-01-01','2017-08-31'))
calendar = calendar.join(holiday_data).fillna(0)
del holiday_data
calendar

calendar['dow'] = calendar.index.dayofweek+1
calendar['workday'] = True
calendar.loc[calendar['dow']>5 , 'workday'] = False

calendar.head()

calendar.loc[(calendar['type']=='Holiday') & (calendar['locale'].str.contains('National')), 'workday'] = False
calendar.loc[(calendar['type']=='Additional') & (calendar['locale'].str.contains('National')), 'workday'] = False
calendar.loc[(calendar['type']=='Bridge') & (calendar['locale'].str.contains('National')), 'workday'] = False
calendar.loc[(calendar['type']=='Transfer') & (calendar['locale'].str.contains('National')), 'workday'] = False

calendar.loc[calendar['type']=='Work Day' , 'workday'] = True
calendar.where(calendar['transferred'] == True).dropna()

calendar.loc[(calendar['transferred'] == True), 'workday'] = True
calendar.where(calendar['description'].str.contains('futbol')).dropna()

calendar['is_football'] = 0
calendar['is_eq'] = 0

calendar.loc[(calendar['is_football'] == 0) & (calendar['description'].str.contains('futbol')), 'is_football'] = 1
calendar.loc[(calendar['is_eq'] == 0) & (calendar['description'].str.contains('Terremoto')), 'is_eq'] = 1
calendar.where(calendar['is_football']==1).dropna().head()

calendar.where(calendar['is_eq']==1).dropna().head()

calendar.loc[calendar['is_football']==1,'description'] = 'football'
calendar.loc[calendar['is_eq']==1,'description'] = 'earthquake'
sales = process_train.groupby('date').sales.sum()
event = calendar[calendar['type']=='Event']

event_merge = event.merge(sales,how='left',left_index=True,right_index=True)
event_merge

del sales
del event

print('mean of daily sale across country: {}'.format(process_train.groupby('date').sales.sum().mean()))

print('--------------------')

print(('mean of sale across country in event day: {}'.format(event_merge.groupby('description').sales.mean())))

calendar.head()

calendar['workday'] = calendar['workday'].map({False:0,True:1})
calendar['transferred'] = calendar['transferred'].map({'False':0,False:0,True:1})
calendar['is_ny'] = 0
calendar['is_christmas'] = 0
calendar['is_shopping'] = 0

calendar.loc[calendar['description'] == 'New Year day', 'is_ny'] = 1
calendar.loc[calendar['description'] == 'Christmas day', 'is_christmas'] = 1
calendar.loc[calendar['description'] == 'Black Friday', 'is_shopping'] = 1
calendar.loc[calendar['description'] == 'Cyber Monday' , 'is_shopping'] = 1
calendar.loc['2014-12-25'].to_frame().T

calendar.head()

locale_dummy = pd.get_dummies(calendar['locale_name'],prefix='holiday_')
calendar = locale_dummy.join(calendar,how='left')
calendar = calendar.drop('locale_name',axis=1)

del locale_dummy
calendar_checkpoint = calendar
calendar_checkpoint = calendar_checkpoint.drop('description',axis = 1)
calendar_checkpoint = calendar_checkpoint[~calendar_checkpoint.index.duplicated(keep='first')] 
calendar_checkpoint = calendar_checkpoint.iloc[:,1:-1]
calendar_checkpoint

del calendar
gc.collect()

oil_data = pd.read_csv("input/oil.csv")
oil_data.head(5)

pd.date_range(start = '2013-01-01', end = '2017-08-15' ).difference(oil_data.index)

oil_data['date'] = pd.to_datetime(oil_data['date'])
oil_data = oil_data.set_index('date')
oil_data = oil_data.resample('1D').sum()
oil_data.reset_index()

pd.date_range(start = '2013-01-01', end = '2017-08-15' ).difference(oil_data.index)

oil_data['dcoilwtico'] = np.where(oil_data['dcoilwtico']==0, np.nan, oil_data['dcoilwtico'])
oil_data['interpolated_price'] = oil_data.dcoilwtico.interpolate()
oil_data = oil_data.drop('dcoilwtico',axis=1)
oil_data.head()

oil_data['price_chg'] = oil_data.interpolated_price - oil_data.interpolated_price.shift(1)
oil_data['pct_chg'] = oil_data['price_chg']/oil_data.interpolated_price.shift(-1)
oil_data.head()

fig,ax = plt.subplots(figsize=(15,5))
plt.plot(oil_data['interpolated_price'])
plt.title('Oil Price over time')
plt.show()

daily_total_sales = total_sales.copy()
daily_total_sales.head()

daily_total_sales = daily_total_sales.resample('1D').sum()
daily_total_sales

oil_data.interpolated_price.loc['2013-01-01':'2017-08-15']

plt.scatter(daily_total_sales,oil_data.interpolated_price.loc['2013-01-01':'2017-08-15'],alpha=0.4)
plt.ylabel('oil price')
plt.xlabel('daily total sales')
plt.show()

daily_total_sales = pd.DataFrame(daily_total_sales)
daily_total_sales['sales_chg'] = daily_total_sales['sales']-daily_total_sales['sales'].shift(1)
daily_total_sales['sales_pct_chg'] = daily_total_sales['sales_chg']/daily_total_sales['sales'].shift(-1)

daily_total_sales.head()

print('Spearman Rank Correlation = {}'.format(
    process_train.sales.corr(process_train.onpromotion,method='spearman')))
    
print('Pearson Correlation between oil price change and total sales change = {}'.format(
oil_data.price_chg.corr(daily_total_sales.sales_chg,method='pearson')))
print('Spearman Rank Correlation between oil price change and total sales change = {}'.format(
oil_data.price_chg.corr(daily_total_sales.sales_chg,method='spearman')))

print('----------------------------------------------------------------------------')

print('Pearson Correlation between % oil price change and % total sales change = {}'.format(
oil_data.pct_chg.corr(daily_total_sales.sales_pct_chg,method='pearson')))
print('Spearman Rank Correlation between oil price change and total sales change = {}'.format(
oil_data.pct_chg.corr(daily_total_sales.sales_pct_chg,method='spearman')))

# Oil lag PACF
import  statsmodels.graphics.tsaplots

ax = statsmodels.graphics.tsaplots.plot_pacf(oil_data.interpolated_price.dropna(), 
                                                 lags=31,
                                                 title = 'oil lag PACF')
                                                 
oil_lag = [10,15,26,27]
for lag in oil_lag:
    oil_data['price_lag_{}'.format(lag)] = oil_data.interpolated_price.shift(lag)

oil_for_lag_coor = oil_data.dropna()
oil_for_lag_coor.head()

oil_for_lag_coor = oil_for_lag_coor.merge(daily_total_sales,how='inner',left_index=True,right_index=True)
oil_for_lag_coor = oil_for_lag_coor[['price_lag_10','price_lag_15','price_lag_26','price_lag_27','sales']]
oil_for_lag_coor.head()

fig, ax = plt.subplots()
lag_col =  ['price_lag_10','price_lag_15','price_lag_26','price_lag_27']

for lag in lag_col:
    plt.scatter(oil_for_lag_coor['sales'],oil_for_lag_coor[lag],alpha=0.30)
    plt.title('Oil Lag {} vs Sales'.format(lag))
    plt.xlabel('oil price lag {}'.format(lag))
    plt.ylabel('amount sold')
    plt.legend()
    plt.show()
    
del [oil_lag,oil_data,oil_for_lag_coor,lag_col]

gc.collect()

transactions = transaction_data.copy()
transactions = transactions.set_index('date')

del transaction_data
transactions.index = pd.to_datetime(transactions.index)
transactions.head()

def transaction_sales_dic(transaction_df,sale_dic):
    transaction_dic = {}
    sale_dict = sale_dic.copy()

    for i in transaction_df['store_nbr'].unique():
        store_transacion = transaction_df.loc[transaction_df['store_nbr'] == i]
        transaction_dic[i] = store_transacion['transactions']
        
    for i in sale_dict.keys():
        sale_dict[i] = sale_dict[i].groupby(['date','store_nbr']).sales.sum()
        sale_dict[i] = sale_dict[i].reset_index()
        sale_dict[i] = sale_dict[i].drop('store_nbr', axis=1)
        sale_dict[i] = sale_dict[i].groupby('date').sales.sum()
            
    return transaction_dic, sale_dict
        
def  series_merge_inner_index(dic1, dic2):
    merged_dic = {}
    for key in dic1.keys():
        merged_dic[key] = dic1[key].to_frame().merge(dic2[key].to_frame(), how='inner',
                                                    left_index=True, right_index=True)
    return merged_dic
  
transaction_dic, sale_dic = transaction_sales_dic(transactions,daily_sale_dict)
merged_sales_transaction = series_merge_inner_index(transaction_dic, sale_dic)
merged_sales_transaction[1]

fig, ax = plt.subplots(figsize=(15,7))
for key in merged_sales_transaction.keys():
    plt.scatter(merged_sales_transaction[key].transactions,
                merged_sales_transaction[key].sales)

plt.title('Transaction vs Amount Sold')
plt.xlabel('transactions number')
plt.ylabel('amount sold')
plt.show()

import  statsmodels.graphics.tsaplots

for store_nbr in merged_sales_transaction.keys():
    ax = statsmodels.graphics.tsaplots.plot_pacf(merged_sales_transaction[store_nbr].transactions, 
                                                 lags=range(16,31),
                                                 title = 'Store {} transactions lag'.format(store_nbr))
                                                 
import  statsmodels.graphics.tsaplots

daily_store_sale_dict = {}
for i in daily_sale_dict.keys():
    daily_store_sale_dict[i] = daily_sale_dict[i].groupby(['date','store_nbr']).sales.sum().to_frame()

del daily_sale_dict

daily_store_sale_dict[1].head()

for i in daily_store_sale_dict.keys():
    daily_store_sale_dict[i] = daily_store_sale_dict[i].droplevel(1) 

for i in daily_store_sale_dict.keys():

    ax = statsmodels.graphics.tsaplots.plot_pacf(daily_store_sale_dict[i],lags=14, 
                                                 title = 'store {} PA'.format(i))
                                                 
process_train

test_data.head()

test_data['sales'] = 0
test_data = test_data[['id','date','store_nbr','family','sales','onpromotion']]

test_data

process_train['id'] = process_train.reset_index().index
process_train = process_train.reset_index()
process_train = process_train[['id','date','store_nbr','family','sales','onpromotion']]
process_train

merged_train = pd.concat([process_train,test_data])
merged_train = merged_train.set_index(['date','store_nbr','family'])
merged_train

merged_train

del test_data
gc.collect()

store_location = store_data.drop(['state','type','cluster'],axis=1)
store_location = store_location.set_index('store_nbr')
store_location = pd.get_dummies(store_location,prefix='store_loc_')
store_location

inputs = merged_train.reset_index().merge(store_location,how='outer',left_on='store_nbr',right_on=store_location.index)
inputs

del store_location
del merged_train
gc.collect()

total_sales

total_sales_to_scale = pd.DataFrame(index=pd.date_range(start='2013-01-01',end='2017-08-31'))
total_sales_to_scale = total_sales_to_scale.merge(total_sales,how='left',left_index=True,right_index=True)
total_sales_to_scale = total_sales_to_scale.rename(columns={'sales':'national_sales'})
total_sales_to_scale

from sklearn.preprocessing import MinMaxScaler
mmScale = MinMaxScaler()
mmScale.fit(total_sales_to_scale['national_sales'].to_numpy().reshape(-1,1))

total_sales_to_scale['scaled_nat_sales'] = mmScale.transform(total_sales_to_scale['national_sales'].to_numpy().reshape(-1,1))
total_sales_to_scale

import  statsmodels.graphics.tsaplots

ax = statsmodels.graphics.tsaplots.plot_pacf(total_sales_to_scale['scaled_nat_sales'].dropna(), 
                                                 lags=range(16,31),
                                                 title = 'PACF of national sales')
                                                 
lags= [16,17,18,19,20,21,22,23,24,27,28]
for lag in lags:
    total_sales_to_scale['nat_scaled_sales_lag{}'.format(lag)] = total_sales_to_scale['scaled_nat_sales'].shift(lag)
total_sales_to_scale = total_sales_to_scale.drop(['national_sales','scaled_nat_sales'],axis=1) 
total_sales_to_scale.reset_index().tail()

inputs = inputs.merge(total_sales_to_scale.reset_index(),how='left',left_on='date',right_on='index')
del total_sales_to_scale
inputs.columns

inputs.drop(['index'],axis=1,inplace=True)
inputs

lags = [1, 2, 3, 4, 5, 6, 7, 8, 13, 14]
for lag in lags:
    inputs['store_fam_sales_lag_{}'.format(lag)] = inputs['sales'].shift(lag)
inputs.columns

transactions

store_nbr = range(1,55)
dates = pd.date_range('2013-01-01','2017-08-31')
mul_index = pd.MultiIndex.from_product([dates,store_nbr],names=['date','store_nbr'])
df = pd.DataFrame(index=mul_index)
df.reset_index()

transactions.reset_index()

df_transaction = df.reset_index().merge(transactions.reset_index(),
                                        how='left',
                                        left_on=['date','store_nbr'],
                                        right_on=['date','store_nbr']
                                       )
df_transaction.fillna(0, inplace=True)
df_transaction.loc[30020:30026]

df_transaction

lags = [21,22,28]
for lag in lags:
    df_transaction['trans_lag_{}'.format(lag)] = df_transaction['transactions'].shift(lag)
df_transaction = df_transaction.drop('transactions',axis=1)
df_transaction = df_transaction.fillna(0)
df_transaction.loc[30030:30040]

inputs

inputs = inputs.merge(df_transaction, how='left', left_on = ['date','store_nbr'],right_on = ['date','store_nbr'])
inputs

calendar_checkpoint.reset_index().tail()

inputs = inputs.merge(calendar_checkpoint,how='left',left_on=['date'],right_on=calendar_checkpoint.index)
inputs.columns

pd.set_option('display.max_rows',None)
inputs.isna().sum()

pd.reset_option('display.max_rows','display.max_columns')
inputs.dropna(inplace = True)
inputs.isna().sum().sum()

inputs = inputs.set_index('date')
inputs.tail()

y_train = inputs.loc['2013-01-01':'2017-08-15', 'sales']
y_train.tail()

x_train = inputs.loc['2013-01-01':'2017-08-15'].drop(['sales','id'],axis=1)
x_train = x_train.reset_index()
x_train = x_train.set_index(['date','store_nbr','family'])
x_train.tail()

x_train.describe()

x_test = inputs.loc['2017-08-16': ]
test_id = x_test['id'] #Keep for later

x_test.drop(['sales','id'],axis = 1,inplace = True)

x_test = x_test.reset_index()
x_test = x_test.set_index(['date','store_nbr','family'])
x_test

sample

test_id

# save sample file+
sample.to_csv('submissiontoday.csv', index = False)
