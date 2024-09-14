from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import sys
import time
import socket
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from .models import *


class SearchLinks:

    def __init__(self, ip=None):
        socket.setdefaulttimeout(30)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.ua_generator = UserAgent()
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--incognito")
        # UserAgent.chrome generará un user-agent aleatorio de Chrome
        self.options.add_argument(f'user-agent={self.ua_generator.chrome}')
        if ip:
            self.options.add_argument('--proxy-server=http://' + ip)
        self.driver = webdriver.Chrome( options=self.options)
        self.driver.get('http://patents.google.com/advanced')
        self.prefix = 'https://patents.google.com/patent/'
        self.number_of_results = None
        self.links = []
        self.titles = []

    def search(self, search_terms):
        try:
            # presence_of_element_located no garantiza que se haya mostrado
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.ID, 'searchInput')))
        except:
            print('Error al cargar https://patents.google.com/advanced')
            sys.exit()
        time.sleep(3)
        self.driver.find_element(By.ID, 'searchInput').send_keys(search_terms)
        time.sleep(3)
        self.driver.find_element(By.ID,'searchButton').click()
        time.sleep(3)
        # Establecer "Results/page" en 100 para obtener menos resultados por página
        
        WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((By.XPATH, '//dropdown-menu[@label="Results / page"]')))
        self.driver.find_element(By.XPATH, '//dropdown-menu[@label="Results / page"]').click()
        self.driver.find_element(By.XPATH, '//dropdown-menu[@label="Results / page"]/'
                                              'iron-dropdown/div/div/div/div[4]').click()
     

    def check_page_loaded(self):
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.XPATH, '//paper-tab/div[@class="tab-content style-scope paper-tab"]')))
        except:
            print('Error al cargar la página de resultados de búsqueda')
            sys.exit()

    def search_links(self):
     self.check_page_loaded()
     if not self.number_of_results:
        num_results_text = self.driver.find_element(By.ID, 'numResultsLabel').text
        num_results_match = re.search(r"\b(\d+)\b", num_results_text)
        self.number_of_results = int(num_results_match.group()) if num_results_match else 0

     link_elements = self.driver.find_elements(By.XPATH,
        '//search-result-item//article//h4[@class="metadata style-scope search-result-item"]//'
        'span[@class="bullet-before style-scope search-result-item"]//'
        'span[@class="style-scope search-result-item"]')
     title_elements = self.driver.find_elements(By.XPATH,
        '//search-result-item//article//state-modifier//a//h3//span')

     self.links.extend([e.text for e in link_elements if e.text != ''])
     self.titles.extend([e.text for e in title_elements if e.text != ''])

    def collect_links(self):
        while True:
            time.sleep(3)
            self.search_links()
            try:
                WebDriverWait(self.driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//iron-icon[@id="icon"]')))
                next_btn = self.driver.find_elements(By.XPATH, '//iron-icon[@id="icon"]')[1]
                if next_btn.is_displayed():
                    next_btn.click()
                else:
                    raise ValueError
            except:
                print('¡Se alcanzó la última página!')
                break

        return self.links, self.titles
    
    
    
    

    def fetch_patent_data(self, link, result_data, not_scraped, fuente1):
        url = f'https://patents.google.com/patent/{link}'
        # Send request to Google Patents and scrap source of patent page
        try:
            r = requests.get(url, headers=self.headers)
        except requests.exceptions.ConnectionError as e:
            not_scraped.append(link)
            print(e, '\n\n')
            return

        # Use BeautifulSoup to extract information from HTML
        bs = BeautifulSoup(r.content, 'html.parser')

        # Find claims section
        claims = bs.find('section', {'itemprop': 'claims'})
        if claims is not None:
            # Handle situation where claims have non-English paragraphs
            if claims.find('span', class_='notranslate') is None:
                claims = claims.text.strip()
            else:
                notranslate = [tag.find(class_='google-src-text') for tag in claims.find_all('span', class_='notranslate')]
                for tag in notranslate:
                    tag.extract()
                claims = claims.text.strip()
        else:
            claims = 'Not Found'

        desc = bs.find('section', {'itemprop': 'description'})
        if desc is not None:
            # Handle situation where description have non-English paragraphs
            if desc.find('span', class_='notranslate') is None:
                desc = desc.text.strip()
            else:
                notranslate = [tag.find(class_='google-src-text') for tag in desc.find_all('span', class_='notranslate')]
                for tag in notranslate:
                    tag.extract()
                desc = desc.text.strip()
        else:
            desc = 'Not Found'

        abst = bs.find('section', {'itemprop': 'abstract'})
        if abst is not None:
            # Handle situation where abstract have non-English paragraphs
            if abst.find('span', class_='notranslate') is None:
                abst = abst.text.strip()
            else:
                notranslate = [tag.find(class_='google-src-text') for tag in abst.find_all('span', class_='notranslate')]
                for tag in notranslate:
                    tag.extract()
                abst = abst.text.strip()
        else:
            abst = 'Not Found'

        patent_office = bs.find('dd', {'itemprop': 'countryName'})
        if patent_office is not None:
            patent_office = patent_office.text
        else:
            patent_office = 'Not Found'

        # Add information to result_data dictionary
        result_data.append({
            'ID': link.split('/')[-1],
            'Abstract': abst,
            'Description': desc,
            'Claims': claims,
            'Patent Office': patent_office,
            'URL': link
        })
        
        for item in result_data:
         ApiPatente.objects.get_or_create(
         id=item['ID'],
         fuente=fuente1, 
         abstract=item['Abstract'],
         description=item['Description'],
         claims=item['Claims'],
         patent_office=item['Patent Office'],
         url=item['URL'])
         
        return result_data

    def collect_patent_data(self, result_data, not_scraped,fuente):
        for i, link in enumerate(self.links):
            self.fetch_patent_data(link, result_data, not_scraped,fuente)

            # Wait 70 seconds every 10 iterations to avoid blocking from Google
            if i % 10 == 0 and i != 0:
                time.sleep(70)



def Google_patent(fuente):
    
  
  # Crear una instancia de SearchLinks
  searcher = SearchLinks()
  # Realizar una búsqueda para obtener todos los resultados posibles
  searcher.search('broom sixty resource salt rock 90  gender')
  # Recopilar los enlaces y títulos de los resultados de búsqueda
  links, titles = searcher.collect_links()
  # Crear una lista para almacenar los resultados
  result_data = []
  not_scraped = []
  # Recopilar los datos de las patentes
  searcher.collect_patent_data(result_data, not_scraped,fuente)
  return result_data



# Imprimir los enlaces y títulos encontrados
#for link, title in zip(links, titles):
#    print(f"Enlace: {link}")
#    print(f"Título: {title}")
#    print("---")

# Imprimir los resultados
#for data in result_data:
#    for item in data:
#      print(item)
      
      
      