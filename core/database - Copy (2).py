import json
from threading import Lock

import time
import pyodbc
import sqlite3
import base64
from datetime import datetime
import os
import cv2
import configparser

from config import ConfigLoader  # for reading config.ini
from logger import LoggerUtility


class EventDatabase:
    _instance = None
    _lock = Lock()  # Thread-safe singleton

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EventDatabase, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path="./config.ini"):
        # Prevent reinitialization
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True

        self.cfg = ConfigLoader()
        obj_logger = LoggerUtility()
        self.logger = obj_logger.get_logger(__name__)

        # Load configuration
        driver = self.cfg.get("DATABASE.driver")
        server = self.cfg.get("DATABASE.server")
        uid = self.cfg.get("DATABASE.uid")
        database = self.cfg.get("DATABASE.database")
        pwd = self.cfg.get("DATABASE.pwd")

        # Establish database connection
    
        self.conn = pyodbc.connect(
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={uid};"
            f"PWD={pwd}",
            autocommit=True
        )

        self.cursor = self.conn.cursor()
        self.logger.info(f"Connected to database: {database} on {server}")

        self.ensure_camera_table_exists()


    def _is_connection_alive(self):
        try:
            if self.conn is None:
                return False
            self.conn.cursor().execute("SELECT 1")
            return True
        except Exception:
            return False

    def _reconnect_if_needed(self):
        if self._is_connection_alive():
            return

        self.logger.warning("DB connection lost. Reconnecting...")

        try:
            driver = self.cfg.get("DATABASE.driver")
            server = self.cfg.get("DATABASE.server")
            uid = self.cfg.get("DATABASE.uid")
            database = self.cfg.get("DATABASE.database")
            pwd = self.cfg.get("DATABASE.pwd")

            self.conn = pyodbc.connect(
                f"DRIVER={driver};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={uid};"
                f"PWD={pwd}",
                autocommit=True
            )

         
            print("_reconnect_if_needed succesfull")

        except Exception as e:
            self.logger.exception("Failed to reconnect DB")
            raise

    def _get_cursor(self):
        self._reconnect_if_needed()
        return self.conn.cursor()


    def ensure_camera_table_exists(self):
        """
        Check if Camera_Details table exists.
        If not, create it automatically.
        """
       
        try:
            # Check table existence
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 1 
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo'
                AND TABLE_NAME = 'Camera_Details'
            """)
                
            table_exists = cursor.fetchone()

            if not table_exists:
                self.logger.info("Camera_Details table NOT found. Creating table...")

                create_query = """
                    CREATE TABLE [dbo].[Camera_Details](
                        [Camera_Id] INT IDENTITY(1,1) PRIMARY KEY,
                        [Camera_Name] VARCHAR(100),
                        [URL] VARCHAR(500),
                        [Camera_UserName] VARCHAR(100),
                        [Camera_IpAddress] VARCHAR(50),
                        [Camera_Password] VARCHAR(100),
                        [Camera_Port] INT,
                        [Camera_Substream] INT
                    );
                """

                cursor.execute(create_query)
                self.logger.info("Camera_Details table created successfully.")
               
            else:
                self.logger.info("Camera_Details table already exists.")

            cursor.close()

        except Exception as e:
            self.logger.exception(f"Failed to verify/create Camera_Details table: {e}")



    

    def insert_notification_if_allowed(self, event_id_str, cam_id, camera_name, relative_image_path, helmet, vest, shoes, time, helmet_color, relative_video_path):
        """
        Insert notification into Notification_Details table.
        Fixed: Removed context manager conflict with persistent cursor.
        """
        try:
            # Convert values to BIT
            def to_bit(value):
                if isinstance(value, (int, bool)):
                    return int(value)
                if isinstance(value, str):
                    return 1 if value.strip().lower() in ["yes", "y", "true", "1"] else 0
                return 0

            helmet, vest, shoes = map(to_bit, (helmet, vest, shoes))

            # Create a new cursor for this operation
            # cursor = self.conn.cursor()
            cursor=self._get_cursor()
            
            cursor.execute("""
                INSERT INTO [PPE_DB].[dbo].[Notification_Details] (
                    Event_Id,
                    Camera_Id,
                    Camera_Name,
                    Image_Path,
                    Helmet,
                    Vest,
                    Shoes,
                    Event_Time,
                    Helmet_Color,
                    Ack_Message,
                    Ack_By,
                    Ack_Time,
                    Video_Path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', NULL, NULL, ?)
            """, (
                str(event_id_str),
                int(cam_id),
                camera_name,
                relative_image_path,
                helmet,
                vest,
                shoes,
                time,
                helmet_color,
                relative_video_path
            ))
            
            cursor.close()
            self.logger.info(f"Notification inserted successfully for Event_Id: {event_id_str}")

        except Exception as e:
            self.logger.exception(f"Failed to insert notification: {e}")

         
    def fetch_Camera_deatils(self):
        """
        Fetch camera details dynamically using FETCH_LIMIT from config.ini.
        """
        
        self.ensure_camera_table_exists()
        
        self.camera_no = int(self.cfg.get("CAMERA.fetch_limit", 4))  # default = 4

        try:
            # Build the query dynamically using Python f-string
            query = f"""
                SELECT TOP {self.camera_no}
                    Camera_Id,
                    Camera_Name,
                    URL
                FROM [PPE_DB].[dbo].[Camera_Details]
            """
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in rows]

        except Exception as e:
            self.logger.exception(f"Failed to fetch camera details: {e}")
            return []
        
    def load_all_camera_roi(self):
        try:
            query = """
                SELECT CameraId, Points
                FROM Camera_ROI
            """
            cursor = self.conn.cursor()
            rows = cursor.execute(query).fetchall()

            camera_roi_map = {}

            for row in rows:
                cam_id = int(row.CameraId)

                # Points stored as JSON string in DB
                pts = json.loads(row.Points)
        

                camera_roi_map[cam_id] = pts

            cursor.close()
            return camera_roi_map

        except Exception as e:
            self.logger.exception(f"Failed to load camera details: {e}")
            return []

            
       


    def fetch_camera_ppe_policy(self):
        """
        Fetch PPE policy per camera:
        - helmet allowed if Event == 1
        - vest allowed if Event == 'yes'
        """
        try:
            query = """
                SELECT Cam_Id, Type, Event
                FROM [PPE_DB].[dbo].[PpePolicy]
            """
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            camera_ppe_policy = {}

            for cam_id, ppe_type, event in rows:
                cam_id = int(cam_id)
                ppe_type = ppe_type.strip().lower()

                # ensure dictionary for each cam_id
                if cam_id not in camera_ppe_policy:
                    camera_ppe_policy[cam_id] = {}

                # Logic for event-based allowance
                if ppe_type == "helmet" and str(event).strip() == "1":
                    camera_ppe_policy[cam_id][ppe_type] = 1
                elif ppe_type == "vest" and str(event).strip().lower() == "yes":
                    camera_ppe_policy[cam_id][ppe_type] = 1
                elif ppe_type not in ["helmet", "vest"]:
                    # for all other PPE types, store event as-is (optional)
                    camera_ppe_policy[cam_id][ppe_type] = int(event) if str(event).isdigit() else event

            return camera_ppe_policy

        except Exception as e:
            self.logger.exception(f"Failed to fetch camera PPE policy: {e}")
            return {}

    def fetch_not_allowed_colors(self):
        """
        Fetch helmet colors where vest and shoes detection are not allowed.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT [Helmet_Color]
                FROM [PPE_DB].[dbo].[HelmetPolicy]
                WHERE [Vest_Detection] = 0 AND [Shoes_Detection] = 0
            """)
            rows = cursor.fetchall()
            cursor.close()
            return [row[0] for row in rows] if rows else []
        
        except Exception as e:
            self.logger.exception(f"Failed to fetch restricted helmet colors: {e}")
            return []
    

    def fetch_last_event_ids(self):
        """
        Fetch the latest Event_Id and Id for each Camera_Id.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    ed.Camera_Id,
                    ed.Id AS Last_Updated_Id,
                    PARSENAME(REPLACE(ed.Event_Id, '_', '.'), 1) AS Event_Number
                FROM [PPE_DB].[dbo].[Event_Details] ed
                INNER JOIN (
                    SELECT 
                        Camera_Id,
                        MAX(Id) AS MaxId
                    FROM [PPE_DB].[dbo].[Event_Details]
                    GROUP BY Camera_Id
                ) latest
                    ON ed.Camera_Id = latest.Camera_Id
                AND ed.Id = latest.MaxId
                ORDER BY ed.Camera_Id;
            """)
            rows = cursor.fetchall()
            cursor.close()

            # Return as list of dictionaries (easy to use)
            return [
                {
                    "camera_id": row[0],
                    "last_updated_id": row[1],
                    "event_id": row[2]
                }
                for row in rows
            ] if rows else []

        except Exception as e:
            self.logger.exception(f"Failed to fetch last event ids: {e}")
            return []


    

    def update_video_path(self, event_id, video_path):
        """
        Updates Video_Path in both:
        - Event_Details
        - Notification_Details
        """
        try:
            if not event_id or not video_path:
                return

            event_id = str(event_id).strip()  # keep Event_Id as string
            cursor = self.conn.cursor()
            
            # Update Event_Details
            cursor.execute("""
                UPDATE PPE_DB.dbo.Event_Details
                SET Video_Path = ?
                WHERE Event_Id = ?
            """, (video_path, event_id))

            # Update Notification_Details (only if exists)
            cursor.execute("""
                UPDATE PPE_DB.dbo.Notification_Details
                SET Video_Path = ?
                WHERE Event_Id = ?
            """, (video_path, event_id))
            
            cursor.close()
            self.logger.info(f"Video path updated successfully for Event_Id: {event_id}")

        except Exception as e:
            self.logger.exception("DB ERROR (Unified Video Path Update):")

       
    
   

    def fetch_Camera_name_deatils(self, n):
        """
        Return camera name from local cached map instead of DB query.
        If any exception occurs, safely return None.
        """
        try:
            # Load the cache only once if not already loaded
            if not hasattr(self, "camera_id_name_map"):
                self.fetch_all_camera_names()

            # Return name if camera_id exists in cached dictionary
            return self.camera_id_name_map.get(n, None)

        except Exception as e:
            self.logger.exception(f"Error fetching camera name for ID {n}: {e}")
            return None
        
    def fetch_all_camera_names(self):
        """Fetch all camera name-id pairs ONCE and store in a dictionary."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT Camera_Id, Camera_Name
                FROM [PPE_DB].[dbo].[Camera_Details]
            """)
            rows = cursor.fetchall()
            cursor.close()
            
            # Store data as a dictionary for quick lookup
            self.camera_id_name_map = {row[0]: row[1] for row in rows}
            self.logger.info("All camera names cached successfully.")
        
        except Exception as e:
            self.logger.exception(f"Failed to fetch all camera names: {e}")
            self.camera_id_name_map = {}

    

    def fetch_Image_folder_path(self):
        """
        Fetch image folder path from Config_Details table.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT Config_Value
                FROM PPE_DB.dbo.Config_Details
                WHERE Config_Key = 'Image_Path'
            """)
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else None

        except Exception as e:
            self.logger.exception(f"Failed to fetch config value: {e}")
            return None
        

    def fetch_Video_folder_path(self):
        """
        Fetch video folder path from Config_Details table.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT Config_Value
                FROM PPE_DB.dbo.Config_Details
                WHERE Config_Key = 'Video_Path'
            """)
            row = cursor.fetchone()
            cursor.close()
          
            return row[0] if row else None

        except Exception as e:
            self.logger.exception(f"Failed to fetch config value: {e}")
            return None
        


    


    def insert_event(self, track_id, camera_id, camera_name, Image_Path, helmet, vest, shoes, helmet_color, relative_video_path, time):
        """
        Insert event into Event_Details table.
        Fixed: Removed context manager conflict with persistent cursor.
        """
        try:
            # Convert values to BIT
            def to_bit(value):
                if isinstance(value, (int, bool)):
                    return int(value)
                if isinstance(value, str):
                    return 1 if value.strip().lower() in ["yes", "y", "true", "1"] else 0
                return 0

            helmet, vest, shoes = map(to_bit, (helmet, vest, shoes))
            
            # Create a new cursor for this operation
            # cursor = self.conn.cursor()
            cursor=self._get_cursor()

            cursor.execute("""
                INSERT INTO [PPE_DB].[dbo].[Event_Details] (
                    Event_Id,
                    Camera_Id,
                    Camera_Name,
                    Image_Path,
                    Helmet,
                    Vest,
                    Shoes,
                    Event_Time,
                    Helmet_Color,
                    Video_Path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                track_id,
                camera_id,
                camera_name,
                Image_Path,
                helmet,
                vest,
                shoes,
                time,
                helmet_color,
                relative_video_path
            ))
            
            cursor.close()
            self.logger.info(f"Event inserted successfully for Event_Id: {track_id}")

        except Exception as e:
            self.logger.exception(f"Failed to insert event: {e}")
            
            


  
       


    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            try:
                self.conn.close()
                self.logger.info("Database connection closed.")
            except Exception as e:
                self.logger.exception(f"[ERROR] close: {e}")