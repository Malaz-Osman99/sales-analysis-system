import sqlite3

def get_connection():
    conn = sqlite3.connect("C:\Users\thela\OneDrive\Desktop\project\sales_analytics_system\data\database\sales.db")
    return conn
