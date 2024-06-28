import requests
import urllib3.util
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import networkx as nx
import warnings
import re
import os
import csv
import time
import urllib.parse
from imdb_helper_functions import first_supp_func_find_cast_of_film, \
    second_supp_func_get_films_of_actor, get_actor_name, plot


'''In this function i cheated a bit and pass the table with the cast, not the whole html page'''
def get_actors_by_movie_soup(cast_page_soup: WebElement, num_of_actors_limit=None) -> dict:
    if cast_page_soup is None:
        return {None:None}
    dict_of_actors, counter = {}, 0
    soup = BeautifulSoup(cast_page_soup)
    table_data = soup.find_all('td', class_=False)
    if num_of_actors_limit is not None and num_of_actors_limit > 0:
        for el in table_data:
            if counter < num_of_actors_limit:
                dict_of_actors[el.text.strip().strip('\n')] = urllib.parse.urljoin("https://www.imdb.com/", el.find_next('a')['href'])
                counter += 1
            else: break
        return dict_of_actors
    elif num_of_actors_limit is None:
        for el in table_data:
            dict_of_actors[el.text.strip().strip('\n')] = urllib.parse.urljoin("https://www.imdb.com/", el.find_next('a')['href'])
    return dict_of_actors


'''second supp funct gets a list of films instead of the whole page'''
def get_movies_by_actor_soup(films_list : list[WebElement], num_of_movies_limit=None) -> dict:
    pairs_dict, counter = {}, 0
    if num_of_movies_limit is not None and num_of_movies_limit > 0:
        for el in films_list :
            if counter < num_of_movies_limit:
                soup = BeautifulSoup(el.get_attribute('innerHTML'))
                title = soup.find('a', class_='ipc-metadata-list-summary-item__t').text
                url = soup.find('a')['href']
                pairs_dict[title] = urllib.parse.urljoin("https://www.imdb.com/", url)
                counter += 1
            else: break
        return pairs_dict
    elif num_of_movies_limit is None:
        for el in films_list :
            soup = BeautifulSoup(el.get_attribute('innerHTML'))
            title = soup.find('a', class_='ipc-metadata-list-summary-item__t').text
            url = soup.find('a')['href']
            pairs_dict[title] =  urllib.parse.urljoin("https://www.imdb.com/", url)
        return pairs_dict

def get_movie_distance(actor_start_url: str, actor_end_url: str, num_of_actors_limit=None, num_of_movies_limit=None, max_distance = None) -> int:
    film_distance, counter = 0, 0
    supp_actors_list, extra_supp_actors_list = [], []
    actor_start_name = get_actor_name(actor_start_url)
    actor_end_name = get_actor_name(actor_end_url)
    with open('distances.csv', mode='a', newline='') as f:
        writer = csv.writer(f)
        while film_distance <= max_distance:
            if not supp_actors_list:
                table_of_films_unprocessed = second_supp_func_get_films_of_actor(
                    actor=actor_start_url)
                table_of_films_final = get_movies_by_actor_soup(table_of_films_unprocessed, num_of_movies_limit=num_of_movies_limit)
                for film in table_of_films_final.keys():
                    cast_soup = first_supp_func_find_cast_of_film(film)
                    actors = get_actors_by_movie_soup(cast_page_soup=cast_soup, num_of_actors_limit=num_of_actors_limit)
                    if actor_end_name in actors:
                        writer.writerow([actor_start_name,actor_start_url, actor_end_name,actor_end_url, film_distance])
                        return film_distance
                    for link in actors.values():
                        supp_actors_list.append(link)
                film_distance += 1
            else:
                for actor in supp_actors_list:
                    if actor is None:
                        continue
                    table_of_films_unprocessed = second_supp_func_get_films_of_actor(
                        actor=actor)
                    table_of_films_final = get_movies_by_actor_soup(table_of_films_unprocessed,
                                                                    num_of_movies_limit=num_of_movies_limit)
                    for film in table_of_films_final.keys():
                        cast_soup = first_supp_func_find_cast_of_film(film)
                        actors = get_actors_by_movie_soup(cast_page_soup=cast_soup, num_of_actors_limit=num_of_actors_limit)
                        if actor_end_name in actors:
                            writer.writerow([actor_start_name,actor_start_url, actor_end_name,actor_end_url, film_distance])
                            return film_distance
                        for link in actors.values():
                            extra_supp_actors_list.append(link)
                supp_actors_list = extra_supp_actors_list
                extra_supp_actors_list = []
                film_distance += 1
        writer.writerow([actor_start_name, actor_start_url, actor_end_name,actor_end_url, 'None'])

def get_movie_descriptions_by_actor_soup(actor_page_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    actor_name = get_actor_name(actor_page_link)
    list_of_descriptions = []
    films_list = second_supp_func_get_films_of_actor(actor=actor_page_link)
    movies_processed = get_movies_by_actor_soup(films_list=films_list)
    with open(f'{actor_name}.csv', mode='w', encoding='utf-8') as f:
        for movie_url in movies_processed.values():
            response = requests.get(movie_url, headers=headers)
            soup = BeautifulSoup(response.text)
            readall_is_present = soup.find('a', class_='ipc-link ipc-link--baseAlt')
            if readall_is_present:
                pattern = r'tt\d+'
                match = re.search(pattern, movie_url)
                if match:
                    imdb_id = match.group(0)
                    new_url = f'https://www.imdb.com/title/{imdb_id}/plotsummary/'
                else:
                    print("unable to get full description, moving to the next movie...")
                    continue
                response = requests.get(new_url, headers=headers)
                soup = BeautifulSoup(response.text)
                description = soup.find('div', class_="ipc-html-content-inner-div")
                inner_description = description.find('div', class_="ipc-html-content-inner-div")
                if inner_description:
                    list_of_descriptions.append(inner_description.text)
                    f.write(inner_description.text+'\n')
                else:
                    list_of_descriptions.append(inner_description.text)
                    f.write(description.string+'\n')
            else:
                paragraph = soup.find('p', attrs={'data-testid':"plot"})
                description = paragraph.find('span', attrs={'data-testid':"plot-l"}).text
                list_of_descriptions.append(description)
                f.write(description+'\n')
    with open(f'{actor_name}.csv', mode='r') as f:
        contents = ''.join(f.readlines())
        stopwords = set(STOPWORDS)
        stopwords.update(['video', 'game', 'player'])
        wordcloud = WordCloud(max_font_size=50, max_words=100, background_color="white", stopwords=stopwords).generate(contents)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
    return list_of_descriptions

def plot_distance(weight_of_edges = None):
    with open('distances.csv', mode='r') as f:
        G = nx.Graph()
        lines = f.readlines()[1:]
        for line in lines:
            elements = line.split(',')
            weight = int(elements[4].rstrip('\n'))
            G.add_nodes_from([elements[0], elements[2]])
            G.add_edge(elements[0], elements[2], weight=weight)
        pos = nx.spring_layout(G)
        # colors_with_distances = {1: 'green', 2: 'red', 3: 'blue'}
        if weight_of_edges == 1:
            plot(color = 'green', weight = 1, G = G, pos = pos)
        elif weight_of_edges == 2:
            plot(color = 'red', weight = 2, G = G, pos = pos)
        elif weight_of_edges == 3:
            plot(color = 'blue', weight = 3, G = G, pos = pos)
        else:
            print('function works with max weight = 3')

if __name__ == '__main__':
    #print(get_actor_name('https://www.imdb.com/name/nm0000138/?ref_=ttfc_fc_cl_t1'))
    # actors by movie
    # cast_soup = first_supp_func_find_cast_of_film('Sinbad and the Cyclops Island')
    # print(get_actors_by_movie_soup(cast_page_soup=cast_soup, num_of_actors_limit=2))
    #films by actor
    # table_of_films = second_supp_func_get_films_of_actor(actor = 'https://www.imdb.com/name/nm0000093/?ref_=nv_sr_srsg_0_tt_0_nm_8_q_brad')
    # print(table_of_films)
    # print(get_movies_by_actor_soup(table_of_films))
    #get_movie_descriptions_by_actor_soup('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1')

    # cast_soup = first_supp_func_find_cast_of_film('Black Widow')
    # print(get_actors_by_movie_soup(cast_page_soup=cast_soup, num_of_actors_limit=10))
    plot_distance()


    #Dwayne Johnson - https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1
    #Chris Hemsworth - https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth
    #Robert Downey Jr. - https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1
    #Akshay Kumar - https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1
    #Jackie Chan - https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1
    #Bradley Cooper - https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1
    #Adam Sandler - https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler
    #Scarlett Johansson - https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1
    #Sofia Vergara - https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1
    #Chris Evans - https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1

    # file_exists = os.path.isfile('distances.csv')
    # if file_exists:
    #     os.remove('distances.csv')
    #print(get_movie_distance('https://www.imdb.com/name/nm0000093/?ref_=nv_sr_srsg_0_tt_0_nm_8_q_brad', 'https://www.imdb.com/name/nm1869101/?ref_=tt_cl_t_2', num_of_movies_limit=2,
                             #num_of_actors_limit=5, max_distance=3))
    #get_movie_distance('https://www.imdb.com/name/nm0000093/?ref_=nv_sr_srsg_0_tt_0_nm_8_q_brad',
                        # 'https://www.imdb.com/name/nm7282126/?ref_=tt_cl_t_1', num_of_movies_limit=2,
                        # num_of_actors_limit=5, max_distance=3)`
    #Dwayne
    #get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1',num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Cris
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Robert
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Akshay
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # # Jackie
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Bradley
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Adam
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Scarlet
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Sofia
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # #Chris
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0425005/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm1165110/?ref_=nv_sr_srsg_0_tt_5_nm_3_q_Chris%2520Hemsworth', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000375/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0474774/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0000329/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0177896/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0001191/?ref_=nv_sr_srsg_0_tt_6_nm_2_q_Adam%2520Sandler', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0424060/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)
    # get_movie_distance('https://www.imdb.com/name/nm0262635/?ref_=fn_al_nm_1','https://www.imdb.com/name/nm0005527/?ref_=fn_al_nm_1', num_of_movies_limit=2,num_of_actors_limit=5, max_distance=3)

