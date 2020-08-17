import sqlite3


class Restaurant:
    """
    Class for restaurant object
    """
    def __init__(self, store_id, latitude, longitude, restaurant_chain):
        self.store_id = store_id
        self.latitude = latitude
        self.longitude = longitude
        self.restaurant_chain = restaurant_chain
        self.rivals = 0

    def add_in_base(self):
        conn = sqlite3.connect('restaurants.db')
        cursor = conn.cursor()
        values = (self.store_id, self.latitude, self.longitude, self.restaurant_chain, self.rivals)
        cursor.execute("""INSERT INTO restaurants
                       VALUES (?,?,?,?,?)""", values)
        conn.commit()
