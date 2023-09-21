# Import Libraries
from tabula.io import read_pdf
import pandas as pd
from datetime import datetime
import PyPDF2


def single_page(page, delta=2):
    """Create data frame frome single pdf page: DBS bank statement template
    Combined with the usage of tabula
    Input: 
    + page: list of lists
    + delta: buffer zone to identify the start of content (in points of pdf)
    """
    
    # Parameter of page area to be used later
    left1 = 45.4
    left2 = 113.1
    start3 = 250.0
    end3 = 397.4 # starting point matters: withdraw
    start4 = end3 # starting point matters: deposit
    end4 = 500 # roughly
    
    # Make empty result table and lists for its columns
    tbl = pd.DataFrame(columns=['Date', 'Description', 'Withdraw', 'Deposite', 'Balance'])
    date_col = []
    desc_col = []
    withdraw_col = []
    depo_col = []
    balance_col = []

    # Create two flag variables to assist looping over data
    prev_date = None  # date of the previous record
    stop = False  # If false: keep collecting information for result table

    # Loop over each row and each column on the page
    for row in page: # loop over each row
        if stop == True:
            break

        for item in row: # loop over each column item
            if (item['left'] > left1 - delta) & (item['left'] < left1 + delta): # first column
                if item['text'][0] in ['0', '1', '2', '3']: # starting letter of date is [0,1,2,3]
                    
                    # Take transaction date
                    if prev_date is not None: 
                        # write down the record values
                        date_col.append(prev_date)
                        desc_col.append(desc)
                        withdraw_col.append(withdraw)
                        depo_col.append(depo)
                        balance_col.append(balance)
                        prev_date = item['text'][:10]

                    date = item['text'][:10]
                    desc = item['text'][11:]
                    withdraw = None
                    depo = None
                    balance = None
                    prev_date = date

            elif (item['left'] > left2 - delta) & (item['left'] < left2 + delta) & (
                prev_date is not None): #second column

                # If reach to end of page: must start with the following phrases
                if (item['text'].find('Balance Carried Forward') == 0) | (
                    item['text'].find('Total Balance Carried Forward in SGD:') == 0):                
                    # end of transaction on the page
                    date_col.append(prev_date)
                    desc_col.append(desc)
                    withdraw_col.append(withdraw)
                    depo_col.append(depo)
                    balance_col.append(balance)
                    stop = True
                else:
                    # take transaction description
                    desc += ' '+ item['text']

            elif (item['left'] > start3 - delta) & (item['left'] < end3 + delta) & (
                prev_date is not None): # third column
                # take transaction withdraw
                withdraw = item['text']

            elif (item['left'] > start4 - delta) & (item['left'] < end4 + delta) & (
                prev_date is not None): # fourth column
                # take transaction deposite and balance
                depo, balance = item['text'].split(' ')

            elif (item['left'] > end4 - delta) & (prev_date is not None): # fifth column
                # take transaction balance
                balance = item['text']

    tbl['Date'] = date_col
    tbl['Description'] = desc_col
    tbl['Withdraw'] = withdraw_col
    tbl['Deposite'] = depo_col
    tbl['Balance'] = balance_col
    tbl.fillna(0, inplace=True)
    
    return tbl


def single_page_citi(page, delta=2):
    """Create data frame frome single pdf page: Citi bank statement template
    Combined with the usage of tabula
    Input: 
    + page: list of lists
    + delta: buffer zone to identify the start of content (in points of pdf)
    """
    
    # Parameter of page area to be used later
    start1 = 46.1
    end1 = 49.7
    start2 = 105.8 

    # Make empty result table and lists for its columns
    tbl = pd.DataFrame(columns=['Date', 'Description', 'Amount'])
    date_col = []
    text_col = []
    desc_col = []
    amt_col = []

    # Create two flag variables to assist looping over data
    prev_date = None  # date of the previous record
    stop = False  # If false: keep collecting information for result table

    # Loop over each row to collect all information on the page
    for row in page: # loop over each row
        if stop == True:
            break

        col_start = False # keep collecting data from each column in a row
        for item in row: # loop over each column item
            if (item['left'] > start1 - delta) & (item['left'] < end1 + delta): # first column
                if item['text'][0] in ['0', '1', '2', '3']: # starting letter of date is [0,1,2,3]
                    # Take transaction date
                    if prev_date is not None: 
                        # write down the record values
                        text_col.append(text)
                        prev_date = item['text'][:6]

                    col_start = True
                    prev_date = item['text'][:6]
                    text = item['text']

            if (item['left'] > start2 - delta) & (col_start == True):
                # information on other columns
                text += ' ' + item['text']

            if ((item['left'] > start2 - delta) & (item['text'] == 'GRAND TOTAL')) |(
                (item['left'] < start1 - delta) & (item['text'][:7] == 'EPSTCSX')):
                # Ending point of the page
                text_col.append(text)
                stop = True

    # Split text into date, description and amount   
    for text in text_col:
        loc = max(text.rfind(' SG '), text.rfind(' US '))

        if loc > 0:
            date, desc, amt = text[:6], text[7:loc].strip(), text[(loc+4):].strip()
        else: 
            date, desc, amt = text[:6], ' '.join(text[7:loc].split(
                ' ')[:-1]).strip(), text.split(' ')[-1].strip()

        date_col.append(date)
        desc_col.append(desc)
        amt_col.append(convert_to_num(amt))

    tbl['Date'] = date_col
    tbl['Description'] = desc_col
    tbl['Amount'] = amt_col
    
    return tbl


def single_page_ocbc(page, delta=2):
    """Create data frame frome single pdf page: OCBC bank statement template
    Combined with the usage of tabula
    Input: 
    + page: list of lists
    + delta: buffer zone to identify the start of content (in points of pdf)
    """
    
    # Parameter of page area to be used later
    start_row = 7
    left1 = 45.4
    start3 = 351
    end3 = 366
    start4 = 434
    end4 = 451

    # Make empty result table and lists for its columns
    tbl = pd.DataFrame(columns=['Date', 'Description', 'Withdraw', 'Deposite'])
    date_col = []
    desc_col = []
    withdraw_col = []
    depo_col = []

    # Flag to indicate the existence of statement
    bf = 0 # Flag of beginning of statement
    cf = 0 # Flag of end of statement

    # Loop over each row and each column on the page
    for row in page[start_row:]: # loop over each row

        for item in row: # loop over each column item
            if (item['text'] == 'BALANCE B/F'): # beginning of statement
                bf += 1
                continue
                
            if (item['text'] == 'BALANCE C/F'): # end of statement
                cf += 1
                break
            elif (item['left'] > left1 - delta) & (item['left'] < left1 + delta): # first column
                # Take date and description information
                date_col.append(item['text'][:6])
                desc_col.append(item['text'][14:])
            elif (item['left'] > start3 - delta) & (item['left'] < end3 + delta): # second column
                # Take withdraw information
                withdraw_col.append(item['text'].split(' ')[0])
                depo_col.append(0)
            elif (item['left'] > start4 - delta) & (item['left'] < end4 + delta): # third column
                # Take deposite information
                withdraw_col.append(0)
                depo_col.append(item['text'].split(' ')[0])

        if (item['text'] == 'BALANCE C/F'): # end of statement, jump out of all page
            break

    if (bf + cf > 0):
        tbl['Date'] = date_col
        tbl['Description'] = desc_col
        tbl['Withdraw'] = [float(str(i).replace(',','')) for i in withdraw_col]
        tbl['Deposite'] = [float(str(i).replace(',','')) for i in depo_col]
        tbl.fillna(0, inplace=True)
        
    return tbl


def single_page_dbscredit(page, delta=2):
    """Create data frame frome single pdf page: DBS bank credit statement template
    Combined with the usage of tabula
    Input: 
    + page: list of lists
    + delta: buffer zone to identify the start of content (in points of pdf)
    """
    
    # Parameter of page area to be used later
    left1 = 54
    
    # Make empty result table and lists for its columns
    tbl = pd.DataFrame(columns=['Date', 'Description', 'Withdraw', 'Deposite'])
    date_col = []
    desc_col = []
    withdraw_col = []
    depo_col = []
    
    # Loop over each row and each column on the page
    for row in page: # loop over each row
        
        if (row[0]['left'] > left1 - delta) & (row[0]['left'] < left1 + delta): # first column
            if row[0]['text'][0] in ['0', '1', '2', '3']: # starting letter of date is [0,1,2,3]
                date = row[0]['text'][:6] # Take transaction date
                desc = row[0]['text'][7:] # description
                
                if row[-1]['text'][-2:] == 'CR': # Check if it is payment or expenditure
                    depo = row[-1]['text'][:-3]
                    withdraw = None
                else:
                    depo = None
                    withdraw = row[-1]['text']

                date_col.append(date)
                desc_col.append(desc)
                withdraw_col.append(withdraw)
                depo_col.append(depo)

    tbl['Date'] = date_col
    tbl['Description'] = desc_col
    tbl['Withdraw'] = withdraw_col
    tbl['Deposite'] = depo_col
    tbl.fillna(0, inplace=True)
    
    return tbl


def single_page_ocbc_list(page, delta=2):
    """Create data frame frome single pdf page: OCBC bank statement template
    Combined with the usage of tabula
    Input: 
    + page: list of lists
    + delta: buffer zone to identify the start of content (in points of pdf)
    """
    
    # Parameter of page area to be used later
    start_row = 7
    left1 = 45.4
    left2 = 136.9
    start3 = 351
    end3 = 366
    start4 = 434
    end4 = 451

    # Make empty result table and lists for its columns
    date_col = []
    desc_col = []
    withdraw_col = []
    depo_col = []

    # Flag to indicate the existence of statement
    bf = 0
    cf = 0

    # Loop over each row and each column on the page
    for row in page[start_row:]: # loop over each row

        for item in row: # loop over each column item
            if (item['text'] == 'BALANCE B/F'): # beginning of statement
                bf += 1
                continue
            if (item['text'] == 'BALANCE C/F'): # end of statement
                cf += 1
                break
            elif (item['left'] > left1 - delta) & (item['left'] < left1 + delta): # first column
                date_col.append(item['text'][:6])
                desc_col.append(item['text'][14:])
            elif (item['left'] > start3 - delta) & (item['left'] < end3 + delta): 
                withdraw_col.append(item['text'].split(' ')[0])
                depo_col.append(0)
            elif (item['left'] > start4 - delta) & (item['left'] < end4 + delta): 
                withdraw_col.append(0)
                depo_col.append(item['text'].split(' ')[0])

        if (item['text'] == 'BALANCE C/F'): # end of statement
            break
        
    return date_col, desc_col, withdraw_col, depo_col


def mod_ocbc_df(filepath, page, box=[3, 1, 27, 30]):
    """Modify the OCBC statement tables due to the formatting issues in original statements"""
    
        
    # Convert box to pdf point: 1 pt = 1/72 inch, 1 inch = 2.54 cm
    fc = 1/2.54*72
    box = [round(i*fc, 2) for i in box]
    
    # Read pdf: need to install java
    # use guess=False to ensure it capture all content in the page
    df = read_pdf(filepath, pages=page_range, area=[box],
                  output_format='json', stream=True, lattice=False, guess=False)
    
    date_col, desc_col, withdraw_col, depo_col = single_page_ocbc_list(df[0]['data'], delta=2)
    
    return date_col, desc_col, withdraw_col, depo_col, df[0]['data']


# Supporting functions
def convert_to_num(text):
    if text[0] == '(':
        text = text.replace('(', '').replace(')', '')
        text = '-' + text        
    text = text.replace(',', '')
    return round(float(text), 2)


def add_year(text, col, year): # For DBS credit, add year to convert into date
    # If the statement has dates in both Dec and Jan (next year)
    if set([i[-3:] for i in tbl['Date']]) == {'DEC', 'JAN'}:
        if text[-3:] == 'JAN': # Use year + 1, if the month is Jan (next year)
            result = text + ' ' + str(year + 1)
        else:
            result = text + ' ' + str(year)
    else:
        result = text + ' ' + str(year)

    return result


def convert_df(filepath, page_range, box=[3, 1, 27, 30], bank='DBS'):
    """Convert PDF pages into a single data frame
    Need to install java first
    Input:
    + filepath: path of pdf file
    + page_range: list of pages to read
    + box: area of each page to read (in cm), format [top, left, bottom, right]
    """
    
    # Convert box to pdf point: 1 pt = 1/72 inch, 1 inch = 2.54 cm
    fc = 1/2.54*72
    box = [round(i*fc, 2) for i in box]
    
    # Read pdf: need to install java
    # use guess=False to ensure it capture all content in the page
    # Format of read_pdf result: df[page][‘data’][row][column][‘text’]
    df = read_pdf(filepath, pages=page_range, area=[box],
                  output_format='json', stream=True, lattice=False, guess=False)
    
    # Convert to data frame
    if bank == 'DBS':
        result = pd.DataFrame()
        for i in range(len(df)):
            if df[i]['data'][0][0]['text'][:19]!='Transaction Details':
                if len(df[i]['data'][0]) > 1:
                    if df[i]['data'][0][1]['text']=='DBS Multiplier Account':
                        result = pd.concat([result, single_page(df[i]['data'])], ignore_index=True)
            else: # start to record transactions
                result = pd.concat([result, single_page(df[i]['data'])], ignore_index=True)
    elif bank == 'Citi':
        result = pd.concat([single_page_citi(df[i]['data']) for i in range(len(df))], ignore_index=True)
    elif bank == 'OCBC':
        result = pd.DataFrame()
        for i in range(len(df)):
            tmp = single_page_ocbc(df[i]['data'])
            if tmp.shape[0] > 0:
                result = pd.concat([result, tmp])
    elif bank == 'DBS Credit':
        result = pd.DataFrame()
        for i in range(len(df)):
            tmp = single_page_dbscredit(df[i]['data'])
            if tmp.shape[0] > 0:
                result = pd.concat([result, tmp])
            
    return result


def post_process(tbl, bank='DBS', year=datetime.today().year, file=None):
    """ Additional processing after converting into data frame
    Input:
    + tbl: data frame
    + bank: different bank template
    + year: parameter for Citi bank statement which doesn't have years
    """
    
    if bank == 'DBS':
        tbl['Date'] = pd.to_datetime(tbl['Date'], dayfirst=True).dt.date
        tbl['Withdraw'] = tbl['Withdraw'].apply(lambda x: convert_to_num(str(x)))
        tbl['Deposite'] = tbl['Deposite'].apply(lambda x: convert_to_num(str(x)))
        tbl['Balance'] = tbl['Balance'].apply(lambda x: convert_to_num(str(x)))
        
        # Process special secenario where 'Withdraw' & 'Deposite' are both zeros:
        # e.g. 'Advice FAST Payment / Receipt 12.60 PAYNOW TRANSFER TO: YELLOW TAGS ENTERPRISE 53034377XYTE 4WL124267725 OTHER'
        if tbl[(tbl['Withdraw']==0) & (tbl['Deposite']==0)].shape[0] > 0:
            for index, row in tbl[(tbl['Withdraw']==0) & (tbl['Deposite']==0)].iterrows():
                withdraw_values = []
                for i in row['Description'].split():
                    try:
                        withdraw_values.append(float(i.replace(',', ''))) # for scenario: 3,000.0
                    except ValueError:
                        pass

                if len(withdraw_values) == 1:
                    tbl.loc[tbl.index==index, 'Withdraw'] = withdraw_values[0]
                else:
                    print('Both Withdraw and Deposite are zeros: Value Error!')
        
        last_balance = tbl.iloc[0]['Balance'] - tbl.iloc[0]['Deposite'] + tbl.iloc[0]['Withdraw']
        summary = f"""
        DBS bank statement: {min(tbl['Date'])} to {max(tbl['Date'])}
        Last Balance: {last_balance}
        Withdraw: {round(tbl['Withdraw'].sum(),2)}
        Deposite: {round(tbl['Deposite'].sum(), 2)}
        Net Change: {round(tbl['Deposite'].sum() - tbl['Withdraw'].sum(), 2)}
        Current Balance: {tbl.iloc[-1]['Balance']}
        Matched: {round(tbl.iloc[-1]['Balance'], 2) == round(
                    last_balance - tbl['Withdraw'].sum() + tbl['Deposite'].sum(), 2)}
        """
    elif bank == 'Citi':
        citiyear = file[-22:-18]
        tbl['Date'] = pd.to_datetime([datetime.strptime(i + ' ' + citiyear, '%d %b %Y') for i in tbl['Date']])
        tbl['Date'] = tbl['Date'].dt.date
        tbl['Withdraw'] = [i if i>0 else 0 for i in tbl['Amount']]
        tbl['Deposite'] = [-i if i<0 else 0 for i in tbl['Amount']]
        tbl.drop(columns=['Amount'], inplace=True)
        
        summary = f"""
        Citi bank statement: {min(tbl['Date'])} to {max(tbl['Date'])}
        Payment: {round(tbl['Deposite'].sum(), 2)}
        Spending: {round(tbl['Withdraw'].sum(), 2)}
        Please validate!                  
        """
        
    elif bank == 'OCBC':
        ocbcyear = file[-6:-4]
        tbl['Date'] = pd.to_datetime([datetime.strptime(i + ' 20' + ocbcyear, '%d %b %Y') for i in tbl['Date']])
        tbl['Date'] = tbl['Date'].dt.date

        summary = f"""
        OCBC bank statement: {min(tbl['Date'])} to {max(tbl['Date'])}
        Payment: {round(tbl['Deposite'].sum(), 2)}
        Spending: {round(tbl['Withdraw'].sum(), 2)}
        Please validate!                  
        """    
        
    elif bank == 'DBS Credit':
        tbl['Date'] = tbl['Date'].apply(lambda x: x + ' ' + str(year))
        tbl['Date'] = pd.to_datetime(tbl['Date'], dayfirst=True).dt.date
        tbl['Withdraw'] = tbl['Withdraw'].apply(lambda x: convert_to_num(str(x)))
        tbl['Deposite'] = tbl['Deposite'].apply(lambda x: convert_to_num(str(x)))
        
        summary = f"""
        OCBC bank statement: {min(tbl['Date'])} to {max(tbl['Date'])}
        Payment: {round(tbl['Deposite'].sum(), 2)}
        Spending: {round(tbl['Withdraw'].sum(), 2)}
        Please validate!  
        """
        
    else:
        print('key in the right bank!')
        
    print(summary)
    
    return tbl

