import networkx as nx
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from bs4 import BeautifulSoup
import time
import urllib.parse
from selenium.webdriver.remote.webelement import WebElement
import re
from collections import defaultdict
import matplotlib.pyplot as plt

def first_supp_func_find_cast_of_film(film_name: str) -> WebElement:
    exec = 'C:\SeleniumDriver\chromedriver.exe'
    chrome_options = Options()
    chrome_options.add_argument("--lang=en-US")
    service = Service(executable_path=exec)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    url = "https://www.imdb.com/"
    driver.get(url)
    search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q")))
    search_box.send_keys(film_name)
    search_box.send_keys(Keys.RETURN)

    first_result = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "ipc-metadata-list-summary-item__t")))
    first_result.click()

    try:
        unwanted = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="sc-b7c53eda-0 dUpRPQ"]')))
        unwanted_soup = BeautifulSoup(unwanted.get_attribute('innerHTML')).find('li', text='TV Series')
        if unwanted_soup:
            return None
    except TimeoutException:
        pass


    cast_link = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,"div[data-testid='title-cast-header']"))
    )

    driver.execute_script("window.scrollBy(0, 1500);")
    time.sleep(1)
    link_to_cast = cast_link.find_element(By.CSS_SELECTOR,'a')

    link_to_cast.click()

    time.sleep(4)
    cast_table = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "cast_list")))
    inner_html = cast_table.get_attribute('innerHTML')
    return inner_html


def second_supp_func_get_films_of_actor(actor:str) -> list[WebElement]:
    filtered_list = []
    exec = 'C:\SeleniumDriver\chromedriver.exe'
    service = Service(executable_path=exec)
    chrome_options = Options()
    chrome_options.add_argument("--lang=en-US")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(actor)
    filter = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class = 'ipc-chip-list__scroller']")))
    actions = ActionChains(driver)
    actions.move_to_element(filter)
    actions.perform()
    driver.execute_script("window.scrollBy(0, 500);")
    list_of_active_buttons = filter.find_elements(By.CSS_SELECTOR,
                                                  "button[class = 'filmography-selected-chip-filter ipc-chip ipc-chip--active ipc-chip--on-base-accent2']")
    for el in list_of_active_buttons:
        soup = BeautifulSoup(el.get_attribute('innerHTML'))
        outer_span = soup.find('span')
        inner_span = outer_span.find('span')
        if inner_span:
            inner_span.decompose()
        button_type = outer_span.text
        if button_type != 'Actor' and button_type != 'Actress':
            actions = ActionChains(driver)
            actions.move_to_element(el)
            time.sleep(2)
            actions.click(el)
            actions.perform()
    try:
        list_is_collapsed = driver.find_element(By.CSS_SELECTOR, 'label[aria-label="Expand Previous"]')
        released_films_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    "div[class='ipc-accordion sc-5cecff0c-0 hlfPbU date-credits-accordion ipc-accordion--base ipc-accordion--dividers-none ipc-accordion--pageSection']")))
        actions = ActionChains(driver)
        actions.move_to_element(released_films_button)
        actions.click(released_films_button)
        actions.perform()
        time.sleep(2)

        #latest changes applied
        actions = ActionChains(driver)
        try:
            see_all_movies_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ipc-see-more__text')))
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(10)
            actions.move_to_element(see_all_movies_button).click()
            actions.perform()
            time.sleep(10)
        except TimeoutException:
            pass

        list_of_unprocessed_films = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            'ul[class = "ipc-metadata-list ipc-metadata-list--dividers-between ipc-metadata-list--base"]')))
        movies = list_of_unprocessed_films.find_elements(By.CSS_SELECTOR,
                                                         'li[class="ipc-metadata-list-summary-item ipc-metadata-list-summary-item--click sc-e73a2ab4-3 gOirDd"]')
        for item in movies:
            soup = BeautifulSoup(item.get_attribute('innerHTML'))
            series = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='TV Series')
            short = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='Short')
            tv_movie = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='TV Movie')
            video = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='Video')
            videogame = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='Video Game')
            tv_special = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='TV Special')
            if not series and not short and not tv_movie and not video and not videogame and not tv_special:
                filtered_list.append(item)
        return filtered_list


    except NoSuchElementException:
        # latest changes applied
        actions = ActionChains(driver)
        see_all_movies_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ipc-see-more__text')))
        try:
            see_all_movies_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'ipc-see-more__text')))
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(10)
            actions.move_to_element(see_all_movies_button).click()
            actions.perform()
            time.sleep(10)
        except TimeoutException:
            pass

        list_of_unprocessed_films = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            'ul[class = "ipc-metadata-list ipc-metadata-list--dividers-between ipc-metadata-list--base"]')))
        movies = list_of_unprocessed_films.find_elements(By.CSS_SELECTOR, 'li[class="ipc-metadata-list-summary-item ipc-metadata-list-summary-item--click sc-e73a2ab4-3 gOirDd"]')
        for item in movies:
            soup = BeautifulSoup(item.get_attribute('innerHTML'))
            series = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='TV Series')
            short = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='Short')
            tv_movie = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='TV Movie')
            video = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='Video')
            videogame = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='Video Game')
            tv_special = soup.find('div', class_="sc-e73a2ab4-0 kBYTwB").find('span', text='TV Special')
            if not series and not short and not tv_movie and not video and not videogame and not tv_special:
                filtered_list.append(item)
        return filtered_list

def get_actor_name(actor_url:str) -> str:
    exec = 'C:\SeleniumDriver\chromedriver.exe'
    service = Service(executable_path=exec)
    driver = webdriver.Chrome(service=service)
    driver.get(actor_url)
    name_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="hero__primary-text"]')))
    name = BeautifulSoup(name_element.get_attribute('innerHTML')).text
    return name


def plot(color: str, weight: int, G: nx.Graph, pos: dict):
    assert type(color) == str, 'color attribute is not a string'
    assert type(weight) == int, 'weight attribute is not an integer'
    distance_colors = {1: 'green', 2: 'orange', 3: 'blue'}
    edges = [(actor1, actor2) for actor1, actor2, data in G.edges(data=True) if data['weight'] == weight]
    nx.draw_networkx_edges(G, pos=pos, edgelist=edges, edge_color=color, width=2)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels={(actor1, actor2): data['weight'] for actor1, actor2, data in G.edges(data=True) if data['weight'] == weight}, font_size=10)
    plt.show()


if __name__ == '__main__':
    print('This is a support library for data scraping final project and you executed it directly which is not what you should do. Please reconsider your actions '
          'and import it instead')