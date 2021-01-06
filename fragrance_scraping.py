import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
from datetime import date
product_lst = []
response = requests.get("https://www.beautyfresh.com/category/fragrance")
soup = BeautifulSoup(response.text, "html.parser")
total_page = soup.select(".pager-item")[-1].getText()
for i in range(int(total_page)):
    response = requests.get("https://www.beautyfresh.com/category/fragrance?page="+(str(i) if i != 0 else ""))
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(".item")
    for item in items:
        brand_name = item.select_one(".brand").getText()
        item_name = item.select_one(".product-title").getText().strip()
        size = re.findall("([0-9]+[.]*[1-9]*)(ml|g)",item_name)
        qty = re.findall("([1-9])[psc]*\W*[x]",item_name)
        if size and qty:
            item_size = str(float(size[0][0])*int(qty[0]))+size[0][1]
        elif size and len(qty) == 0:
            item_size = size[0][0]+size[0][1]
        else:
            item_size = ''
        item_price = item.find_all('span', class_='uc-price')[-1].getText()[1:].replace(",","")
        available = False if item.select_one(".joinwaitinglist") else True
        if item.select_one(".more-colors"):
            url = "https://www.beautyfresh.com"+item.find('a')['href']
            more = requests.get(url)
            acc_nid = re.findall(r'value="([0-9]+)"', str(more.text))[0]
            more_soup = BeautifulSoup(more.text, "html.parser")
            options = more_soup.find_all("option")
            for option in options:
                item_size = option.getText()
                data = {"attributes[Size]":item_size,"aac_nid": acc_nid}
                headers = {"Referer": url}
                r = requests.post("https://www.beautyfresh.com/uc_aac",headers=headers,data=data)
                prices = re.findall(r"'uc-price\\'>S(\$\d.*?)<", str(r.content))
                item_price = prices[1][1:] if len(prices) > 1 else prices[0][1:]
                available = False if re.findall(r'outofstock',str(r.content)) else True
                product_lst.append([brand_name,item_name,item_size, item_price,available])
        else:    
            product_lst.append([brand_name,item_name,item_size, item_price,available])
fragrance = pd.DataFrame(data=product_lst,columns=["brand_name","item_name","item_size","item_price","available"])
fragrance.index = fragrance.index+1
fragrance['item_price'] = fragrance['item_price'].astype('float')

# Include the discount information
discount = {
    'Clinique': 35,
    'Acqua Di Parma': 35,
    'Chloe': 45,
    'Montblanc': 45,
    'Gucci': 45,
    'Issey': 45,
    'Calvin Klein': 55,
    'Marc Jacobs': 55,
    'Bvlgari': 55,
    'Lanvin': 55,
    'Annick Goutal': 55,
    'Prada': 55   
}

# Applying discount
fragrance['discount'] = fragrance['brand_name'].apply(lambda x:discount.get(x,0))
fragrance['final_price'] = fragrance['item_price']*(100-fragrance['discount'])/100

# Export to csv for storage
fragrance.to_csv(str(date.today())+".csv",header=False)
