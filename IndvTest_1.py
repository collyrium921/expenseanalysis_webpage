import pandas as pd
import numpy as np
import sys
class Test:
    def df_fn(self,data):
        import datetime
        from datetime import date,timedelta 
        df=pd.read_excel(data) 

        #Bank Identification
        if df.apply(lambda x: x.str.contains('IFSC').any()).sum()==1:
            col=df.apply(lambda x: x.str.contains('IFSC').any()).idxmax()
            if df[df[col].str.contains('IFSC',na=False)].apply(lambda x: x.str.contains('HDFC').any()).sum()==1:
                Bank='HDFC'
        elif df.apply(lambda x: x.str.contains('Indian Financial System').any()).sum()==1:
            col=df.apply(lambda x: x.str.contains('Indian Financial System').any()).idxmax()
            if df[df[col].str.contains('Indian Financial System',na=False)].apply(lambda x: x.str.contains('SBIN').any()).sum()==1:
                Bank='SBI'
        else:
            Bank='ICICI'

        #HDFC Bank
        if Bank=='HDFC':
            i1=df[df['Unnamed: 1']=='Narration'].index.values.astype(int)[0]
            df=df.drop(df.index[0:i1])
            df=df.drop([i1+1])
            df= df.drop([df.columns[0]], axis='columns')
            df.rename(columns=df.iloc[0], inplace = True)
            df.drop([i1], inplace = True)
            df=df.reset_index()
            df.drop('index', axis=1, inplace=True)
            df=df.iloc[:df.Narration.isnull().values.argmax()]
            df=df.rename(columns={'Value Dt':'Date','Narration': 'Description','Withdrawal Amt.':'Debit','Deposit Amt.':'Credit','Closing Balance':'Balance'})
            df['Bank']=Bank
            del df['Chq./Ref.No.']

        #ICICI Bank
        if Bank=='ICICI':
            i1=df[df['Unnamed: 1']=='S No.'].index.values.astype(int)[0]
            df=df.drop(df.index[0:i1])
            df= df.drop([df.columns[0]], axis='columns')
            df.rename(columns=df.iloc[0], inplace = True)
            df.drop([i1], inplace = True)
            df=df.reset_index()
            df.drop('index', axis=1, inplace=True)
            df=df.iloc[:df['Transaction Remarks'].isnull().values.argmax()]
            df=df.rename(columns={'Transaction Date': 'Date','Transaction Remarks': 'Description','Withdrawal Amount (INR )':'Debit','Deposit Amount (INR )':'Credit','Balance (INR )':'Balance'})
            df['Bank']=Bank
            del df['S No.']
            del df['Value Date']
            del df['Cheque Number']

        #SBI Bank
        if Bank=='SBI':
            i1=df[df['Unnamed: 2']=='Description'].index.values.astype(int)[0]
            df=df.drop(df.index[0:i1])
            df= df.drop([df.columns[0]], axis='columns')
            df.rename(columns=df.iloc[0], inplace = True)
            df.drop([i1], inplace = True)
            df=df.reset_index()
            df.drop('index', axis=1, inplace=True)
            df=df.iloc[:df['Description'].isnull().values.argmax()]
            df=df.rename(columns={'Value Date': 'Date','        Debit':'Debit'})
            df[['Credit','Debit']]=df[['Credit','Debit']].replace(' ',0)
            df['Debit']=df['Debit'].astype(float)
            df['Credit']=df['Credit'].astype(float)
            df['Balance']=df['Balance'].astype(float)
            df['Bank']=Bank
            del df['Ref No./Cheque No.']

        #Date Adjustment
        df['Date']= pd.to_datetime(df['Date'],dayfirst=True)
        day_start=pd.Timestamp(df.at[0,'Date']).day         
        next_month = (df.at[0,'Date'].replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        day_end=pd.Timestamp(df.at[df.index[-1],'Date']).day
        from pandas.tseries.offsets import MonthEnd
        previous_month=pd.to_datetime(df.at[df.index[-1],'Date'], format="%Y%m") + MonthEnd(-1)
        df=df.set_index('Date')
        max_ind=df.index.max()
        min_ind=df.index.min()
        max_ind=pd.to_datetime(max_ind)
        min_ind=pd.to_datetime(min_ind)
        #First Day
        if day_start <17:
            first_day=min_ind.replace(day=1).strftime('%Y-%m-%d')
        else:
            first_day=next_month
        #Last Day
        import datetime
        from calendar import monthrange
        if day_end >14:
            _,num_days = monthrange(pd.Timestamp(max_ind).year, pd.Timestamp(max_ind).month)
            last_day = datetime.date(pd.Timestamp(max_ind).year, pd.Timestamp(max_ind).month, num_days)
            last_day=last_day.strftime('%Y-%m-%d')
        else:
            last_day=previous_month
        dfx=pd.DataFrame(index=pd.date_range(start=first_day,end=last_day, freq='D'))
        df = dfx.join(df)
        df=df.reset_index()
        df=df.rename(columns={'index': 'Date'})


        df['Description'].fillna('Balance brought forward',inplace=True)        

        dt_df=pd.DataFrame(df.groupby('Date')['Description'].unique())
        dt_df=dt_df.reset_index()

        for i in range(len(dt_df)):
            ind=df.index[df['Date']==dt_df.at[i,'Date']][-1] 
            if ind<df.index[-1]:
                line = pd.DataFrame({"Date": df.at[ind+1,'Date'] , "Description": 'Balance brought forward'}, index=[ind+0.5])
                df = df.append(line, ignore_index=False)
                df = df.sort_index().reset_index(drop=True)       

        df['Debit'].fillna(0, inplace=True)
        df['Credit'].fillna(0, inplace=True)

        n=df.index[df['Description']!='Balance brought forward'][0] 
        if n!=0:
            df.at[n-1,'Balance']=df.at[n,'Balance']+df.at[n,'Debit']-df.at[n,'Credit']

        import math
        if n==0:
            pr_bal=df.at[0,'Balance']+df.at[0,'Debit']-df.at[0,'Credit']

            for q in range(1,len(df)):
                if math.isnan(df.at[q,'Balance']):
                    df.at[q,'Balance']=float(df.at[(q-1),'Balance']) 

        else:
            for i in range(n,len(df)):
                if math.isnan(df.at[i,'Balance']):
                    df.at[i,'Balance']=float(df.at[(i-1),'Balance'])

        if n!=0:
            for i in range(0,n-1):
                df.at[i,'Balance']=df.at[n-1,'Balance']

        df['Description'] = df['Description'].astype('str')

        #Quarters
        for i in range(len(df)):        
            year=pd.Timestamp(df.at[i,'Date']).year
            month=pd.Timestamp(df.at[i,'Date']).month
            df.at[i,'Month-Year']=(((year-2000)*100)+month)
            if month in [1,2,3]:
                df.at[i,'Quarter']=((year-2000)*10)+1
            if month in [4,5,6]:
                df.at[i,'Quarter']=((year-2000)*10)+2
            if month in [7,8,9]:
                df.at[i,'Quarter']=((year-2000)*10)+3
            if month in [10,11,12]:
                df.at[i,'Quarter']=((year-2000)*10)+4

        #Txn Category    
        for i in range(len(df)):
            df.at[i,'Txn Category']='Other'
            inft=['INFT']
            if any(map(df.at[i,'Description'].__contains__, inft)):
                df.at[i,'Txn Category']='INFT'
                df.at[i,'Txn Mode']='Online'

            neft=['NEFT']
            if any(map(df.at[i,'Description'].__contains__, neft)):
                df.at[i,'Txn Category']='NEFT'
                df.at[i,'Txn Mode']='Online' 

            imps=['IMPS']
            if any(map(df.at[i,'Description'].__contains__, imps)):
                df.at[i,'Txn Category']='IMPS'
                df.at[i,'Txn Mode']='Online'

            tpt_list=['TPT']
            if any(map(df.at[i,'Description'].__contains__, tpt_list)):
                df.at[i,'Txn Category']='TPT'
                df.at[i,'Txn Mode']='Offline'

            eba_list=['EBA/']
            if any(map(df.at[i,'Description'].__contains__, eba_list)):
                df.at[i,'Txn Category']='ICICI DIRECT'
                df.at[i,'Txn Mode']='Online'

            cash_list=['CASH DEP','BY CASH','CSH DEP','CASH DEPOSIT']
            if any(map(df.at[i,'Description'].__contains__, cash_list)):
                if df.at[i,'Debit']==0:
                    df.at[i,'Txn Category']='Cash'
                    df.at[i,'Txn Mode']='Offline'

            if df.at[i,'Txn Category']=='Other':
                if df.at[i,'Bank']=='HDFC':
                    atm_other_list=['NWD-','EAW-','ATS-','NFS-','AWB-']
                    if (any(map(df.at[i,'Description'].__contains__, atm_other_list)) & (df.at[i,'Credit']==0)):
                        df.at[i,'Txn Category']='ATM-Other'
                        df.at[i,'Txn Mode']='Offline'
                    atm_own_list=['ATW-']
                    if (any(map(df.at[i,'Description'].__contains__, atm_own_list)) & (df.at[i,'Credit']==0)):
                        df.at[i,'Txn Category']='ATM-Own'
                        df.at[i,'Txn Mode']='Offline'
                    pos_list=['POS ']
                    if (any(map(df.at[i,'Description'].__contains__, pos_list)) & (df.at[i,'Credit']==0)):
                        df.at[i,'Txn Category']='POS'

            if df.at[i,'Txn Category']=='Other':
                if df.at[i,'Bank']=='ICICI':        
                    atm=['CASH WDL']
                    if (any(map(df.at[i,'Description'].__contains__, atm)) & (df.at[i,'Credit']==0)):
                        atm_other_list=['VAT','NFS','MAT','CAM']
                        if (any(map(df.at[i,'Description'].__contains__, atm_other_list))):
                            df.at[i,'Txn Category']='ATM-Other'
                            df.at[i,'Txn Mode']='Offline'
                        else:
                            df.at[i,'Txn Category']='ATM-Own'
                            df.at[i,'Txn Mode']='Offline'
                    pos_list=['VPS','IPS','IIN','VIN','MPS','MIN']
                    if (any(map(df.at[i,'Description'].__contains__, pos_list)) & (df.at[i,'Credit']==0)):
                        df.at[i,'Txn Category']='POS'

            if df.at[i,'Txn Category']=='Other':
                if df.at[i,'Bank']=='SBI':
                    atm=['ATM ']
                    if (any(map(df.at[i,'Description'].__contains__, atm)) & (df.at[i,'Credit']==0)):
                        atm_own_list=['SBI ']
                        if (any(map(df.at[i,'Description'].__contains__, atm_own_list))):
                            df.at[i,'Txn Category']='ATM-Own'
                            df.at[i,'Txn Mode']='Offline'
                        else:
                            df.at[i,'Txn Category']='ATM-Other'
                            df.at[i,'Txn Mode']='Offline'
                    pos_list=['POS','YONO']
                    if (any(map(df.at[i,'Description'].__contains__, pos_list)) & (df.at[i,'Credit']==0)):
                        df.at[i,'Txn Category']='POS'    

            if df.at[i,'Txn Category']=='POS':
                    pos_online=['IIN','VIN','YONO','MIN']
                    if (any(map(df.at[i,'Description'].__contains__, pos_online)) & (df.at[i,'Credit']==0)):
                        df.at[i,'Txn Mode']='Online'
                    else:
                        df.at[i,'Txn Mode']='Offline'

            upi=['UPI','PAYTM','Paytm']
            if df.at[i,'Txn Category']=='Other':
                if any(map(df.at[i,'Description'].__contains__, upi)):
                    df.at[i,'Txn Category']='UPI'
                    df.at[i,'Txn Mode']='Online'

            inft_list=['INTEREST','CRV','REF','REVERSE','REV','Rev','RVSL','Refund','CHGS','CHG','CHARGES','Charges','Closure Proceeds','FD/RD','FD THROUGH NET','FD','RD','Int','TDR']
            if df.at[i,'Txn Category']=='Other':
                if any(map(df.at[i,'Description'].__contains__, inft_list)):
                    df.at[i,'Txn Category']='INFT'
                    df.at[i,'Txn Mode']='Online'

            neft_list=['NEFT','SALARY','SALRY','BIL','MSI','AUTOPAY SI-TAD','AUTOPAY SI-MAD','CMS','GST','CSHFRE','BILLDK','RAZP','CCA','PAYU','ATOM','CITRUS','PAYGT','TECH','FTMF','TEMP MF','ICICI LOMBARD','SBIGEN','EMI','REIMB','PENSIO','INCETICE','LENGRT','FNF','FRANKLINTEMPLETON','RPI','TO TRANSFER-','BY TRANSFER','VSI','ACH','CLG']
            if df.at[i,'Txn Category']=='Other':
                if any(map(df.at[i,'Description'].__contains__, neft_list)):
                    df.at[i,'Txn Category']='NEFT'
                    df.at[i,'Txn Mode']='Online' 

            si_uk=['SI','NET BANKING SI']
            if df.at[i,'Txn Category']=='Other':
                if any(map(df.at[i,'Description'].__contains__, si_uk)):
                    df.at[i,'Txn Category']='NEFT'
                    df.at[i,'Txn Mode']='Online'

        df.loc[df['Description']=='Balance brought forward', 'Txn Category'] = "None"
        df['Quarter']=df['Quarter'].astype(int)
        df['Month-Year']=df['Month-Year'].astype(int)

        for i in range(len(df)):
            df.at[i,'Txn Mode']='Offline'
            if (df.at[i,'Txn Category']=='ATM-Other' or df.at[i,'Txn Category']=='ATM-Own'):
                df.at[i,'Txn Mode']='Offline'
            if df.at[i,'Txn Category']=='POS':
                pos_offline=['POS','VPS','IPS','POS ']
                if (any(map(df.at[i,'Description'].__contains__, pos_offline)) & (df.at[i,'Credit']==0)):
                    df.at[i,'Txn Mode']='Offline'
                else:
                    df.at[i,'Txn Mode']='Online'
            online_list=['UPI','IMPS','INFT','ICICI DIRECT','Charges']
            if (any(map(df.at[i,'Txn Category'].__contains__, online_list))):
                df.at[i,'Txn Mode']='Online'
            online_des=['/IB','IB ','NETBANK','NETBANKING','SBIGEN','TDR','-INB','CHARGES','BANKING SI -TRANSFER','BILLD','DEBIT CARD ANNUAL','REV ','TEMP MF','AUTOPAY','INTEREST CREDIT','NET BANKING']
            if (any(map(df.at[i,'Description'].__contains__, online_des))):
                df.at[i,'Txn Mode']='Online'
            if df.at[i,'Description']=='Balance brought forward':
                df.at[i,'Txn Mode']='None'

        df['Bank Cost']=0
        mdr=0.017
        si=['SI','NET BANKING SI','SI-MAD','BANKING SI']
        for i in range(len(df)):
            if (any(map(df.at[i,'Description'].__contains__,si))):
                df.at[i,'Bank Cost']=-25
            if df.at[i,'Txn Category']=='POS':
                df.at[i,'Bank Cost']=(-1)*(mdr*df.at[i,'Debit'])
            if df.at[i,'Txn Category']=='NEFT':
                if df.at[i,'Txn Mode']=='Offline':
                    if df.at[i,'Bank']=='HDFC':
                        if 0<df.at[i,'Debit']<=100000:
                            df.at[i,'Bank Cost']=-2
                        if 100000<df.at[i,'Debit']:
                            df.at[i,'Bank Cost']=-10 
                    if df.at[i,'Bank']=='ICICI':
                        if 0<df.at[i,'Debit']<=10000:
                            df.at[i,'Bank Cost']=-2.25
                        if 10000<df.at[i,'Debit']<=100000:
                            df.at[i,'Bank Cost']=-4.75
                        if 100000<df.at[i,'Debit']<=200000:
                            df.at[i,'Bank Cost']=-14.75
                        if 200000<df.at[i,'Debit']<=1000000:
                            df.at[i,'Bank Cost']=-24.75
            if df.at[i,'Txn Category']=='IMPS':
                if df.at[i,'Bank']=='HDFC' or df.at[i,'Bank']=='ICICI':
                    if 0<df.at[i,'Debit']<=100000:
                        df.at[i,'Bank Cost']=-5
                    if 100000<df.at[i,'Debit']:
                        df.at[i,'Bank Cost']=-15  
            if df.at[i,'Txn Category']=='TPT':
                if df.at[i,'Bank']=='HDFC':
                    if df.at[i,'Txn Mode']=='Offline':
                        if 0<df.at[i,'Debit']<=100000:
                            df.at[i,'Bank Cost']=-2
                        if 100000<df.at[i,'Debit']:
                            df.at[i,'Bank Cost']=-10
            if df.at[i,'Txn Category']=='Charges':
                df.at[i,'Bank Cost']=float((-1)*df.at[i,'Debit'])

        #Count
        df['Debit Count']=0
        df['Credit Count']=0
        for i in range(len(df)):
            if df.at[i,'Debit']>0:
                df.at[i,'Debit Count']=1
            if df.at[i,'Credit']>0:
                df.at[i,'Credit Count']=1

        df.fillna(df['Bank'].unique()[0],inplace=True)
        df['Bank']= df['Bank'].fillna(Bank)

        minbal_df=pd.DataFrame(df.groupby(['Date','Month-Year','Quarter','Bank'])['Balance'].min())
        minbal_df=minbal_df.reset_index()
        minbal_df['Interest on MinBal']=0
        minbal_df['Interest on MinBal']=minbal_df['Interest on MinBal'].astype(float)
        import calendar
        for i in range(len(minbal_df)):
            if minbal_df.at[i,'Bank']=='SBI':
                if calendar.isleap(minbal_df.at[i,"Date"].year):
                    minbal_df.at[i,'Interest on MinBal']=float(minbal_df.at[i,'Balance']*(0.027/366))
                else:
                    minbal_df.at[i,'Interest on MinBal']=float(minbal_df.at[i,'Balance']*(0.027/365)) 
            else:
                if minbal_df.at[i,'Balance']<5000000:
                    if calendar.isleap(minbal_df.at[i,"Date"].year):
                        minbal_df.at[i,'Interest on MinBal']=float(minbal_df.at[i,'Balance']*(0.03/366))
                    else:
                        minbal_df.at[i,'Interest on MinBal']=float(minbal_df.at[i,'Balance']*(0.03/365))
                else:
                    if calendar.isleap(minbal_df.at[i,"Date"].year):
                        minbal_df.at[i,'Interest on MinBal']=float(minbal_df.at[i,'Balance']*(0.035/366))
                    else:
                        minbal_df.at[i,'Interest on MinBal']=float(minbal_df.at[i,'Balance']*(0.035/365))
        minbal_df.rename(columns = {'Balance':'Minimum Balance'}, inplace = True)

        import calendar
        clbal_df_final=pd.DataFrame()
        df1=df.copy()
        df1.drop_duplicates('Date', keep='last',inplace=True)
        clbal_df = df1[['Date','Month-Year','Quarter','Bank','Balance']]
        clbal_df=clbal_df.reset_index()
        clbal_df['Interest on ClBal']=0
        clbal_df['Interest on ClBal']=clbal_df['Interest on ClBal'].astype(float)

        for i in range(len(clbal_df)):
            if clbal_df.at[i,'Bank']=='SBI':
                if calendar.isleap(clbal_df.at[i,"Date"].year):
                    clbal_df.at[i,'Interest on ClBal']=float(clbal_df.at[i,'Balance']*(0.027/366))
                else:
                    clbal_df.at[i,'Interest on ClBal']=float(clbal_df.at[i,'Balance']*(0.027/365)) 
            else:
                if clbal_df.at[i,'Balance']<5000000:
                    if calendar.isleap(clbal_df.at[i,"Date"].year):
                        clbal_df.at[i,'Interest on ClBal']=float(clbal_df.at[i,'Balance']*(0.03/366))
                    else:
                        clbal_df.at[i,'Interest on ClBal']=float(clbal_df.at[i,'Balance']*(0.03/365))
                else:
                    if calendar.isleap(clbal_df.at[i,"Date"].year):
                        clbal_df.at[i,'Interest on ClBal']=float(clbal_df.at[i,'Balance']*(0.035/366))
                    else:
                        clbal_df.at[i,'Interest on ClBal']=float(clbal_df.at[i,'Balance']*(0.035/365)) 

        clbal_df_final=clbal_df_final.append(clbal_df)
        clbal_df_final=clbal_df_final.reset_index()
        clbal_df_final.drop('index', axis=1, inplace=True)
        clbal_df_final.drop('level_0', axis=1, inplace=True) 
        sub_df = pd.DataFrame(clbal_df_final[['Balance', 'Interest on ClBal']])
        sub_df.rename(columns = {'Balance':'Closing Balance'}, inplace = True)
        bal_int_df=pd.concat([minbal_df, sub_df], axis=1).reindex(minbal_df.index)

        bal_int_df['Month-Year']=bal_int_df['Month-Year'].astype(int)
        #return bal_int_df
        
        
        for i in range (len(df)):
            if df.at[i,'Txn Category']=='ATM-Own':
                if df.at[i,'Bank']=='SBI':
                    if clbal_df_final[clbal_df_final['Month-Year']==df.at[i,'Month-Year']]['Balance'].mean()<=25000:
                        atm_own_df=pd.DataFrame(pd.DataFrame(df[(df['Txn Category'] == 'ATM-Own') & (df['Month-Year']==df.at[i,'Month-Year'])]))
                        atm_own_df=atm_own_df.reset_index()
                        atm_own_df['Count'] = np.arange(len(atm_own_df))
                        for n in range(len(atm_own_df)):
                            if atm_own_df.at[n,'Count']<5:
                                atm_own_df.at[n,'Bank Cost']=10
                            else:
                                atm_own_df.at[n,'Bank Cost']=-10
                        p=(atm_own_df.loc[atm_own_df['Description'] == df.at[i,'Description'], 'Debit'].index.values.astype(int)[0])
                        df.at[i,'Bank Cost']=atm_own_df.at[p,'Bank Cost']
                    else:
                        df.at[i,'Bank Cost']=10
                if df.at[i,'Bank']=='HDFC' or df.at[i,'Bank']=='ICICI':
                    atm_own_df=pd.DataFrame(pd.DataFrame(df[(df['Txn Category'] == 'ATM-Own') & (df['Month-Year']==df.at[i,'Month-Year'])]))
                    atm_own_df=atm_own_df.reset_index()
                    atm_own_df['Count'] = np.arange(len(atm_own_df))
                    for n in range(len(atm_own_df)):
                        if atm_own_df.at[n,'Count']<5:
                            atm_own_df.at[n,'Bank Cost']=20
                        else:
                            atm_own_df.at[n,'Bank Cost']=-20
                    p=(atm_own_df.loc[atm_own_df['Description'] == df.at[i,'Description'], 'Debit'].index.values.astype(int)[0])
                    df.at[i,'Bank Cost']=atm_own_df.at[p,'Bank Cost']

            if df.at[i,'Txn Category']=='ATM-Other':
                if df.at[i,'Bank']=='SBI':
                    if clbal_df_final[clbal_df_final['Month-Year']==df.at[i,'Month-Year']]['Balance'].mean()<=100000:
                        atm_other_df=pd.DataFrame(pd.DataFrame(df[(df['Txn Category'] == 'ATM-Other') & (df['Month-Year']==df.at[i,'Month-Year'])]))
                        atm_other_df=atm_other_df.reset_index()
                        atm_other_df['Count'] = np.arange(len(atm_other_df))
                        for n in range(len(atm_other_df)):
                            if atm_other_df.at[n,'Count']<3:
                                atm_other_df.at[n,'Bank Cost']=20
                            else:
                                atm_other_df.at[n,'Bank Cost']=-20
                        p=(atm_other_df.loc[atm_other_df['Description'] == df.at[i,'Description'], 'Debit'].index.values.astype(int)[0])
                        df.at[i,'Bank Cost']=atm_other_df.at[p,'Bank Cost']
                    else:
                        df.at[i,'Bank Cost']=20
                if df.at[i,'Bank']=='HDFC' or df.at[i,'Bank']=='ICICI':
                    atm_other_df=pd.DataFrame(pd.DataFrame(df[(df['Txn Category'] == 'ATM-Other') & (df['Month-Year']==df.at[i,'Month-Year'])]))
                    atm_other_df=atm_other_df.reset_index()
                    atm_other_df['Count'] = np.arange(len(atm_other_df))
                    for n in range(len(atm_other_df)):
                        if atm_other_df.at[n,'Count']<3:
                            atm_other_df.at[n,'Bank Cost']=20
                        else:
                            atm_other_df.at[n,'Bank Cost']=-20
                    p=(atm_other_df.loc[atm_other_df['Description'] == df.at[i,'Description'], 'Debit'].index.values.astype(int)[0])
                    df.at[i,'Bank Cost']=atm_other_df.at[p,'Bank Cost']

        df['Txn Category'].replace('ATM-Other', 'ATM',inplace=True)
        df['Txn Category'].replace('ATM-Own', 'ATM',inplace=True)
        
        #Customer Cost
        cost1=df.copy()
        self.cost_df=pd.DataFrame(cost1[cost1['Bank Cost']<0].groupby('Txn Category')['Bank Cost'].sum())
        self.cost_df=self.cost_df.reset_index()
        self.cost_df.rename(columns = {'Bank Cost':'Cost'}, inplace = True)
        self.cost_df['Cost']=(-1)*self.cost_df['Cost']

        #Interest df
        self.int_df=pd.DataFrame(round((bal_int_df.groupby('Month-Year')[['Interest on MinBal','Interest on ClBal']].sum()).astype(int)))
        self.int_df=self.int_df.reset_index()
    
        #Balance df
        self.bal_df=pd.DataFrame(round(bal_int_df.groupby('Month-Year')[['Minimum Balance','Closing Balance']].mean()).astype(int))
        self.bal_df=self.bal_df.reset_index()
        
        #Interest and Balance df
        self.balintcombo_df=pd.concat([self.bal_df, self.int_df[['Interest on MinBal','Interest on ClBal']]], axis=1)
        self.balintcombo_df=self.balintcombo_df[['Month-Year','Minimum Balance','Interest on MinBal','Closing Balance','Interest on ClBal']]
        
        #txn_df
        self.txn_df=pd.DataFrame(round(df.groupby(['Txn Category','Month-Year'])['Debit'].sum()/df.groupby(['Txn Category','Month-Year'])['Debit Count'].sum()))
        self.txn_df=self.txn_df.reset_index()
        self.txn_df=self.txn_df.set_index('Txn Category')
        self.txn_df.rename(columns = {0:'Average Debit'}, inplace = True) 
        self.txn_df.drop(['Other','None'], inplace=True)
        self.txn_df=self.txn_df.reset_index()
        cd_df=pd.DataFrame(round(df.groupby(['Txn Category','Month-Year'])['Credit'].sum()/df.groupby(['Txn Category','Month-Year'])['Credit Count'].sum()))
        cd_df=cd_df.reset_index()
        cd_df=cd_df.set_index('Txn Category')
        cd_df.rename(columns = {0:'Average Credit'}, inplace = True) 
        cd_df.drop(['Other','None'], inplace=True)
        cd_df=cd_df.reset_index()
        self.txn_df['Average Credit']=cd_df['Average Credit']
        self.txn_df.fillna(0,inplace=True)
        self.txn_df['Average Debit']=self.txn_df['Average Debit'].astype(int)
        self.txn_df['Average Credit']=self.txn_df['Average Credit'].astype(int)
        
    def txndf(self,category):
        if category=='ATM':
            print(self.txn_df[self.txn_df['Txn Category']=='ATM'])
        if category=='NEFT':
            print(self.txn_df[self.txn_df['Txn Category']=='NEFT'])
        if category=='IMPS':
            print(self.txn_df[self.txn_df['Txn Category']=='IMPS'])
        if category=='POS':
            print(self.txn_df[self.txn_df['Txn Category']=='POS'])
        if category=='UPI':
            print(self.txn_df[self.txn_df['Txn Category']=='UPI'])
        if category=='TPT':
            print(self.txn_df[self.txn_df['Txn Category']=='TPT'])
        if category=='INFT':
            print(self.txn_df[self.txn_df['Txn Category']=='INFT'])
        if category=='ICICI Direct':
            print(self.txn_df[self.txn_df['Txn Category']=='ICICI DIRECT'])
        
    def costdf(self):
        print(self.cost_df)

    def balintdf(self):
        print(self.balintcombo_df)
    
if __name__ == "__main__":
    args = sys.argv[1:3]
    #%load_ext autoreload
    #%autoreload 2
    if(len(args)==2):     
        c = Test()
        c.df_fn(sys.argv[1])
        c.balintdf()
        c.txndf(sys.argv[2])
        c.costdf()
    if(len(args)==1):
        c = Test()
        c.df_fn(sys.argv[1])
        c.balintdf()
        c.costdf()    
    