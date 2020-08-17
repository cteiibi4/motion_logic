import requests
import sqlite3
import folium
import math
import json
import re
from common.restaurant import Restaurant
from common.common import MOSCOW_LATITUDE, MOSCOW_LONGITUDE, MOSCOW_RADIUS, R_EARTH, RIVAL_RADIUS, COLORS


def create_bk_rest():
    """ This function parsed burger king sites, create objects restaurant and add in base"""
    restaurant_chain = 'BK'
    response = requests.get('https://burgerking.ru/restaurant-locations-json-reply-new/')
    rough_response = response.text[2:-2:1].split('},{')
    for i in rough_response:
        str_restaurant = '{' + i + '}'
        rest = json.loads(str_restaurant)
        distance = calculate_distance(float(rest['latitude']), float(rest['longitude']),
                                      MOSCOW_LATITUDE, MOSCOW_LONGITUDE)
        if distance <= MOSCOW_RADIUS:
            restaurant = Restaurant(store_id=rest['storeId'], latitude=rest['latitude'],
                                    longitude=rest['longitude'], restaurant_chain=restaurant_chain)
            restaurant.add_in_base()


def create_kfc_rest():
    """ This function parsed kfc sites, create objects restaurant and add in base"""
    restaurant_chain = 'KFC'
    store_id = 0
    response = requests.get('https://www.kfc.ru/restaurants')
    rough_response = response.text
    pattern_coordinates = r'"coordinates":\[\d+\.\d+,\d+\.\d+\]'  # "coordinates":[55.780761,49.212986]
    pattern_id = r'"storeId":"(\d{8})"'
    result = re.findall(pattern_coordinates, rough_response)
    rough_result_id = re.findall(pattern_id, rough_response)
    result_id = list(set(rough_result_id))
    for i in result:
        store_id = result_id[result.index(i)]
        rest = json.loads('{' + i + '}')
        latitude = rest['coordinates'][0]
        longitude = rest['coordinates'][1]
        distance = calculate_distance(latitude, longitude, MOSCOW_LATITUDE, MOSCOW_LONGITUDE)
        if distance <= MOSCOW_RADIUS:
            restaurant = Restaurant(store_id=store_id, latitude=latitude,
                                    longitude=longitude, restaurant_chain=restaurant_chain)
            restaurant.add_in_base()


def calculate_distance(latitude1, longitude1, latitude2, longitude2):
    """
    This function wait latitude and longitude from 2 point
    and calculated distance
    """
    # translate coordinates in radians
    lat1 = latitude1 * math.pi / 180
    lat2 = latitude2 * math.pi / 180
    long1 = longitude1 * math.pi / 180
    long2 = longitude2 * math.pi / 180
    # calculate cos, sin and delta
    cl1 = math.cos(lat1)
    cl2 = math.cos(lat2)
    sl1 = math.sin(lat1)
    sl2 = math.sin(lat2)
    delta = long2 - long1
    cdelta = math.cos(delta)
    sdelta = math.sin(delta)
    # calculate long for big circle
    y = math.sqrt(pow(cl1 * sdelta, 2) + pow(cl1 * sl2 - sl1 * cl2 * cdelta, 2))
    x = sl1 * sl2 + cl1 * cl2 * cdelta

    ad = math.atan2(y, x)
    distance = ad * R_EARTH
    return distance


def find_rivals(restaurant_chain):
    """
    Take coordinates restaurants from base
    and calculate how more rivals for this restaurant from other chain
     """
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    sql = 'SELECT * FROM restaurants WHERE restaurant_chain=?'
    cursor.execute(sql, [restaurant_chain])
    all_chain_restaurant = cursor.fetchall()
    sql_not = 'SELECT * FROM restaurants WHERE restaurant_chain!=?'
    cursor.execute(sql_not, [restaurant_chain])
    all_rivals_restaurant = cursor.fetchall()
    for restaurant in all_chain_restaurant:
        latitude = restaurant[1]
        longitude = restaurant[2]
        rival = restaurant[4]
        id_st = restaurant[0]
        for rival_restaurant in all_rivals_restaurant:
            latitude_rival = rival_restaurant[1]
            longitude_rival = rival_restaurant[2]
            distance = calculate_distance(latitude, longitude, latitude_rival, longitude_rival)
            if distance <= RIVAL_RADIUS:
                rival += 1
        if rival != 0:
            values = (rival, id_st)
            update_sql = '''UPDATE restaurants
                SET rivals = ? 
                WHERE store_id = ?'''
            cursor.execute(update_sql, values)
            conn.commit()


def color_for_markers(number):
    # Just assign color for marker
    if number <= len(COLORS):
        return COLORS[number]
    else:
        return ('black')


def crete_table():
    # Create table for restaurants in base
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    sql = cursor.execute("""CREATE TABLE restaurants
    (store_id integer, latitude numeric, longitude numeric,
     restaurant_chain text, rivals integer)"""
                         )
    conn.commit()


def drop_table():
    # Delete table from base
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('DROP table if exists restaurants')


def crete_map():
    """Create map and markers"""
    moscow_map = folium.Map(location=[MOSCOW_LATITUDE, MOSCOW_LONGITUDE], zoom_start=11)
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    sql = 'SELECT * FROM restaurants WHERE restaurant_chain="BK"'
    cursor.execute(sql)
    restaurants = cursor.fetchall()
    for i in restaurants:
        folium.Marker(location=[i[1], i[2]], icon=folium.Icon(color=color_for_markers(i[4]))).add_to(moscow_map)
    moscow_map.save("Moscow.html")


if __name__ == '__main__':
    crete_table()
    create_bk_rest()
    create_kfc_rest()
    find_rivals('BK')
    crete_map()
    drop_table()
