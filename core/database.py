import time
import pyodbc
import sqlite3
import base64
from datetime import datetime


import os
import cv2

 
class EventDatabase:
    def __init__(self, db_path="./resource/events_new.db"):
 
        self.conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=ITDT14;'
                'DATABASE=FR_DB_NEW;'
                'UID=sa;'
                'PWD=root1234'
            )
        self.cursor = self.conn.cursor()
 
 
        # self.conn = pyodbc.connect(
        #     'DRIVER={ODBC Driver 17 for SQL Server};'
        #     'SERVER=your_server_name;'
        #     'DATABASE=PPE_DB_NEW;'
        #     'UID=your_username;'
        #     'PWD=your_password'
        # )
        # self.cursor = self.conn.cursor()
 
    # def fetch_latest_events(self, limit=10):
    
    #     try:
    #         self.cursor.execute(f"""
    #             SELECT TOP {limit} event_id, camera_name, image_frame, helmet, vest, shoes
    #             FROM [PPE_DB_NEW].[dbo].[event_details]
    #             ORDER BY event_id DESC
    #         """)
    #         rows = self.cursor.fetchall()
 
    #         # Convert each row to a tuple (for easy access and compatibility with set/list)
    #         event_list = [tuple(row) for row in rows]
    #         print("fetching detztika 10 data_______________________")
 
    #         print(f"Fetched {len(event_list)} latest events.")
    #         return event_list
    #     except Exception as e:
    #         print(f"Failed to fetch latest events: {e}")
    #         return []

    def fetch_latest_events(self, limit=10):
        try:
            self.cursor.execute(f"""
                SELECT TOP {limit} 
                    event_id, 
                    camera_name, 
                    image_frame, 
                    helmet, 
                    vest, 
                    shoes, 
                    event_timestamp   -- ✅ fetch timestamp
                FROM [PPE_DB_NEW].[dbo].[event_details]
                ORDER BY event_id DESC
            """)
            rows = self.cursor.fetchall()

            # Convert each row to a tuple (for easy access and compatibility with set/list)
            event_list = [tuple(row) for row in rows]
            # print("📡 Fetching latest events...")
            # print(f"✅ Fetched {len(event_list)} latest events.")
            return event_list
        except Exception as e:
            print(f"❌ Failed to fetch latest events: {e}")
            return []

        

    # def fetch_latest_All_events(self, limit=20):
    
    #     try:
    #         self.cursor.execute(f"""
    #             SELECT TOP {limit} event_id, camera_name, image_frame, helmet, vest, shoes
    #             FROM [PPE_DB_NEW].[dbo].[event_details]
    #             ORDER BY event_id DESC
    #         """)
    #         rows = self.cursor.fetchall()
 
    #         # Convert each row to a tuple (for easy access and compatibility with set/list)
    #         event_list_all = [tuple(row) for row in rows]
    #         print("fetching detztika 10 data_______________________")
 
    #         print(f"Fetched {len(event_list_all)} latest events.")
    #         return event_list_all
    #     except Exception as e:
    #         print(f"Failed to fetch latest events: {e}")
    #         return []
        

    def fetch_latest_All_events(self, limit=20):
        try:
            self.cursor.execute(f"""
                SELECT TOP {limit} 
                    event_id, 
                    camera_name, 
                    image_frame, 
                    helmet, 
                    vest, 
                    shoes, 
                    event_timestamp   -- ✅ include timestamp
                FROM [PPE_DB_NEW].[dbo].[event_details]
                ORDER BY event_id DESC
            """)
            rows = self.cursor.fetchall()

            # Convert each row to a tuple (for easy access and compatibility with set/list)
            event_list_all = [tuple(row) for row in rows]
            # print("📡 Fetching latest events (All)...")
            # print(f"✅ Fetched {len(event_list_all)} latest events.")
            return event_list_all
        except Exception as e:
            print(f"❌ Failed to fetch latest events: {e}")
            return []
        

    


    
        
    # def fetch_aAl_events(self):
    #     print("fetch_all_events")
    
    #     try:
    #         self.cursor.execute(f"""
    #             SELECT * event_id, camera_name, image_frame, helmet, vest, shoes
    #             FROM [PPE_DB_NEW].[dbo].[event_details]
    #             ORDER BY event_id DESC
    #         """)
    #         rows = self.cursor.fetchall()
 
    #         # Convert each row to a tuple (for easy access and compatibility with set/list)
    #         event_list = [tuple(row) for row in rows]
    #         print("fetching detztika 10 data_______________________")
 
    #         print(f"Fetched {len(event_list)} latest events.")
    #         return event_list
    #     except Exception as e:
    #         print(f"Failed to fetch latest events: {e}")
    #         return []
        
    
 
 
    # def insert_event(self, camera_name, image_frame, helmet, vest, shoes):
    #     try:
    #         # Check number of existing rows
    #         self.cursor.execute("SELECT COUNT(*) FROM [PPE_DB_NEW].[dbo].[event_details]")
    #         count = self.cursor.fetchone()[0]

    #         if count >= 500:
    #             print("⚠️ Limit reached — deleting oldest event.")
    #             self.cursor.execute("""
    #                 DELETE FROM [PPE_DB_NEW].[dbo].[event_details]
    #                 WHERE event_id IN(
    #                     SELECT TOP 400 event_id FROM [PPE_DB_NEW].[dbo].[event_details]
    #                     ORDER BY event_id ASC
    #                 )
    #             """)
    #             self.conn.commit()

    #         # Insert new event
    #         self.cursor.execute("""
    #             INSERT INTO [PPE_DB_NEW].[dbo].[event_details] (
    #                 camera_name,
    #                 image_frame,
    #                 helmet,
    #                 vest,
    #                 shoes
    #             )
    #             VALUES (?, ?, ?, ?, ?)
    #         """, (
    #             camera_name,
    #             image_frame,
    #             helmet,
    #             vest,
    #             shoes
    #         ))
    #         self.conn.commit()
    #         # print(f"✅ Inserted event successfully.")
    #     except Exception as e:
    #         print(f"❌ Failed to insert event: {e}")
    

    def insert_event(self, camera_name, image_frame, helmet, vest, shoes):
        try:
            # Check number of existing rows
            self.cursor.execute("SELECT COUNT(*) FROM [PPE_DB_NEW].[dbo].[event_details]")
            count = self.cursor.fetchone()[0]
            # event_timestamp=datetime.now()
            event_timestamp=int(time.time()) 
          

            if count >= 500:
                print("⚠️ Limit reached — deleting oldest event.")
                self.cursor.execute("""
                    DELETE FROM [PPE_DB_NEW].[dbo].[event_details]
                    WHERE event_id IN(
                        SELECT TOP 400 event_id FROM [PPE_DB_NEW].[dbo].[event_details]
                        ORDER BY event_id ASC
                    )
                """)
                self.conn.commit()

            # Insert new event with timestamp
            self.cursor.execute("""
                INSERT INTO [PPE_DB_NEW].[dbo].[event_details] (
                    camera_name,
                    image_frame,
                    helmet,
                    vest,
                    shoes,
                    event_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                camera_name,
                image_frame,
                helmet,
                vest,
                shoes,
                event_timestamp   # ✅ current timestamp
            ))
            self.conn.commit()
            # print(f"✅ Inserted event successfully.")
        except Exception as e:
            print(f"❌ Failed to insert event: {e}")


    
    
        def close(self):
            if hasattr(self, 'db'):
                try:
                    self.db.close()
                except Exception as e:
                    print(f"[ERROR] close: {e}")
