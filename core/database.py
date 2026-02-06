import datetime
import json
import os
from pathlib import Path
import shutil
from threading import Lock
import threading
import time

import pyodbc



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
        self.image_path = None
        self.camera_id_name_map = {}
        self.camera_roi_map = {}  
        self.camera_ppe_policy = {}
        self.helemt_color_not_allowed = None
        



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
        self.fetch_all_camera_names()
        self.load_all_camera_roi()    
        self.fetch_camera_ppe_policy()
        self.fetch_not_allowed_colors()
        # retension_cleanuo= threading.Thread(target=self.cleanup_Retension_data, daemon=True)
        # retension_cleanuo.start()
    
    def get_image_path(self):
        if self.image_path is not None:
            return self.image_path
        else:
            self.image_path = self.fetch_Image_folder_path()
            return self.image_path
       



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
               
            else:
                self.logger.info("Camera_Details table already exists.")

            cursor.close()

        except Exception as e:
            self.logger.exception(f"Failed to verify/create Camera_Details table: {e}")

    
    # def cleanup_Retension_data(self):
    #     """
    #     Cleanup old PPE data based on RETENTION_DAYS config.
    #     Deletes:
    #     - Old records from Notification_Details and Event_Details
    #     - Old image/video files
    #     - Entire date-named folders (format YYYY-MM-DD) under camera folders
    #     """

    #     import os
    #     import shutil
    #     import datetime
    #     while True:
    #         time.sleep(5)

    #         try:
    #             cursor = self._get_cursor()
    #             print("hello")

    #             # 1️⃣ Get retention days from Config_Details
    #             cursor.execute("""
    #                 SELECT Config_Value
    #                 FROM PPE_DB.dbo.Config_Details
    #                 WHERE Config_Key = 'RetentionDays'
    #             """)
    #             row = cursor.fetchone()

    #             if not row:
    #                 print("RetentionDays not found in Config_Details. Cleanup skipped.")
    #                 return

    #             retention_days = int(row[0])
    #             cutoff_date = datetime.datetime.now().date() - datetime.timedelta(days=retention_days)

    #             print(f"[Cleanup] RetentionDays = {retention_days}")
    #             print(f"[Cleanup] Deleting data before {cutoff_date}")

    #             # 2️⃣ Delete old records from DB (order matters!)
    #             # Delete notifications first
    #             cursor.execute("""
    #                 DELETE FROM PPE_DB.dbo.Notification_Details
    #                 WHERE Event_Time < ?
    #             """, cutoff_date)
    #             deleted_notifications = cursor.rowcount
    #             print(f"Deleted notifications: {deleted_notifications}")

    #             # Delete events
    #             cursor.execute("""
    #                 DELETE FROM PPE_DB.dbo.Event_Details
    #                 WHERE Event_Time < ?
    #             """, cutoff_date)
    #             deleted_events = cursor.rowcount
    #             print(f"Deleted events: {deleted_events}")

    #             cursor.commit()
    #             cursor.close()

    #             # 3️⃣ Delete date-based folders (format YYYY-MM-DD) under camera folders
    #             base_dirs = [
    #                 self.fetch_Image_folder_path(),
    #                 self.fetch_Video_folder_path()
    #             ]

    #             for base_dir in base_dirs:
    #                 if not base_dir or not os.path.exists(base_dir):
    #                     continue

    #                 for cam_dir in os.listdir(base_dir):
    #                     cam_path = os.path.join(base_dir, cam_dir)
    #                     if not os.path.isdir(cam_path):
    #                         continue

    #                     for date_folder in os.listdir(cam_path):
    #                         date_path = os.path.join(cam_path, date_folder)
    #                         if not os.path.isdir(date_path):
    #                             continue

    #                         try:
    #                             # Parse folder name as date
    #                             folder_date = datetime.datetime.strptime(date_folder, "%Y-%m-%d").date()

    #                             if folder_date < cutoff_date:
    #                                 shutil.rmtree(date_path)
    #                                 print(f"Deleted folder: {date_path}")

    #                         except ValueError:
    #                             # Skip folders not matching YYYY-MM-DD
    #                             continue
    #                         except Exception as e:
    #                             print(f"Failed to delete folder {date_path}: {e}")
            
    #             print("[Cleanup] Retention cleanup completed ✅")

    #         except Exception as e:
    #             print(f"[Cleanup] Cleanup failed ❌: {e}")

    
    
    # import os
    # import shutil
    # import datetime
    # import time
    # from pathlib import Path

    # def cleanup_Retension_data(self):
    #     while True:
    #         try:
    #             cursor = self._get_cursor()
    #             cursor.execute("""
    #                 SELECT Config_Value
    #                 FROM PPE_DB.dbo.Config_Details
    #                 WHERE Config_Key = 'RetentionDays'
    #             """)
    #             row = cursor.fetchone()
    #             cursor.close()

    #             if not row:
    #                 print("[Cleanup] RetentionDays not found, skipping cycle")
    #                 time.sleep(1)  # wait 1 hour before next attempt
    #                 continue

    #             retention_days = int(row[0])
    #             cutoff_date = datetime.datetime.now().date() - datetime.timedelta(days=retention_days)

    #             print(f"[Cleanup] Cutoff date: {cutoff_date}")

    #             # Delete DB records first
    #             cursor = self._get_cursor()
    #             cursor.execute("DELETE FROM PPE_DB.dbo.Notification_Details WHERE Event_Time < ?", cutoff_date)
    #             cursor.execute("DELETE FROM PPE_DB.dbo.Event_Details WHERE Event_Time < ?", cutoff_date)
    #             cursor.close()

    #             # Folder cleanup
    #             base_dirs = [
    #                 self.fetch_Image_folder_path(),
    #                 self.fetch_Video_folder_path()
    #             ]

    #             for base_dir in base_dirs:
    #                 if not base_dir or not os.path.exists(base_dir):
    #                     continue

    #                 for cam_dir in os.listdir(base_dir):
    #                     cam_path = os.path.join(base_dir, cam_dir)
    #                     if not os.path.isdir(cam_path):
    #                         continue

    #                     for date_folder in os.listdir(cam_path):
    #                         date_path = os.path.join(cam_path, date_folder)
    #                         if not os.path.isdir(date_path):
    #                             continue

    #                         try:
    #                             # folder_date = datetime.datetime.strptime(date_folder, "%Y-%m-%d").date()
    #                             folder_date = datetime.datetime.strptime(date_folder, "%d-%m-%Y").date()


    #                             # Delete completely if older than retention
    #                             if cam_dir < cutoff_date:
    #                                 delete_old_folders(base_dir,cutoff_date,"%d-%m-%Y")
                                

    #                         except ValueError:
    #                             continue  # skip non-date folders

    #             print("[Cleanup] Completed ✅")

    #         except Exception as e:
    #             print(f"[Cleanup] Failed ❌: {e}")

    #         time.sleep(1)  # Run every hour

    
    # def cleanup_Retension_data(self):
    #     import os
    #     import shutil
    #     import datetime
    #     import time

    #     while True:
    #         try:
    #             cursor = self._get_cursor()
    #             print("[Cleanup] Started")

    #             cursor.execute("""
    #                 SELECT Config_Value
    #                 FROM PPE_DB.dbo.Config_Details
    #                 WHERE Config_Key = 'RetentionDays'
    #             """)
    #             row = cursor.fetchone()

    #             if not row:
    #                 print("[Cleanup] RetentionDays not found, skipping cycle")
    #                 cursor.close()
    #                 time.sleep(6)
    #                 continue

    #             retention_days = int(row[0])
    #             cutoff_date = datetime.datetime.now().date() - datetime.timedelta(days=retention_days)

    #             # Delete DB records
    #             cursor.execute("""
    #                 DELETE FROM PPE_DB.dbo.Notification_Details
    #                 WHERE Event_Time < ?
    #             """, cutoff_date)

    #             cursor.execute("""
    #                 DELETE FROM PPE_DB.dbo.Event_Details
    #                 WHERE Event_Time < ?
    #             """, cutoff_date)

    #             cursor.close()

    #             # Folder cleanup
    #             base_dirs = [
    #                 self.fetch_Image_folder_path(),
    #                 self.fetch_Video_folder_path()
    #             ]

    #             for base_dir in base_dirs:
    #                 if not base_dir or not os.path.exists(base_dir):
    #                     continue

    #                 for cam_dir in os.listdir(base_dir):
    #                     cam_path = os.path.join(base_dir, cam_dir)
    #                     if not os.path.isdir(cam_path):
    #                         continue

    #                     for date_folder in os.listdir(cam_path):
    #                         date_path = os.path.join(cam_path, date_folder)
    #                         if not os.path.isdir(date_path):
    #                             continue

    #                         try:
    #                             folder_date = datetime.datetime.strptime(
    #                                 date_folder, "%Y-%m-%d"
    #                             ).date()

    #                             # 🔥 KEEP only folders inside retention window
    #                             if folder_date < cutoff_date:
    #                                 shutil.rmtree(date_path)
    #                                 print(f"[Cleanup] Deleted folder: {date_path}")

    #                         except ValueError:
    #                             # Not a date folder → ignore
    #                             continue

    #             print("[Cleanup] Completed ✅")

    #         except Exception as e:
    #             print(f"[Cleanup] Failed ❌: {e}")

    #         # # ⏱ run every 5 hours
    #         time.sleep(6)

        

    
    def cleanup_Retension_data(self):
        """
        Cleanup old PPE data based on RETENTION_DAYS config.
        Deletes:
        - Old images & videos
        - Records from Notification_Details
        - Records from Event_Details
        - Empty folders
        """

        try:
            cursor = self._get_cursor()

            # 1️⃣ Get retention days
            cursor.execute("""
                SELECT Config_Value
                FROM PPE_DB.dbo.Config_Details
                WHERE Config_Key = 'RetentionDays'
            """)
            row = cursor.fetchone()

            if not row:
                print("RETENTION_DAYS not found")
                # self.logger.warning("RETENTION_DAYS not found. Cleanup skipped.")
                return

            retention_days = int(row[0])
            print(retention_days)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

            print("cleanup started")

            # # # 2️⃣ Fetch old file paths
            cursor.execute("""
                SELECT Image_Path, Video_Path
                FROM PPE_DB.dbo.Event_Details
                WHERE Event_Time < ?
            """, cutoff_date)

            rows = cursor.fetchall()
            cursor.close()

            image_paths = [r[0] for r in rows if r[0]]
            video_paths = [r[1] for r in rows if r[1]]

            # # 3️⃣ Delete files safely
            def safe_delete(path):
                try:
                    if path and os.path.exists(path):
                        os.remove(path)
                        self.logger.info(f"Deleted file: {path}")
                      
                except Exception as e:
                  self.logger.warning(f"Failed to delete {path}: {e}")

            for p in image_paths:
               
                safe_delete(p)

            for p in video_paths:
              
                safe_delete(p)

            # 4️⃣ Delete DB records (ORDER MATTERS)
            cursor = self._get_cursor()

            cursor.execute("""
                DELETE FROM PPE_DB.dbo.Notification_Details
                WHERE Event_Time < ?
            """, cutoff_date)

            cursor.execute("""
                DELETE FROM PPE_DB.dbo.Event_Details
                WHERE Event_Time < ?
            """, cutoff_date)

            cursor.close()

            # 5️⃣ Cleanup empty folders
            base_dirs = [
                self.fetch_Image_folder_path(),
                self.fetch_Video_folder_path()
            ]

            for base_dir in base_dirs:
                if not base_dir or not os.path.exists(base_dir):
                    continue

                for root, dirs, files in os.walk(base_dir, topdown=False):
                    if not dirs and not files:
                        try:
                            os.rmdir(root)
                        except Exception:
                            pass

        except Exception as e:
            self.logger.exception(f"Cleanup failed ❌: {e}")
       



    

    # def insert_notification_if_allowed(self, event_id_str, cam_id, camera_name, relative_image_path, helmet, vest, shoes, time, helmet_color, relative_video_path):
    #     """
    #     Insert notification into Notification_Details table.
    #     Fixed: Removed context manager conflict with persistent cursor.
    #     """
    #     try:
    #         # Convert values to BIT
    #         def to_bit(value):
    #             if isinstance(value, (int, bool)):
    #                 return int(value)
    #             if isinstance(value, str):
    #                 return 1 if value.strip().lower() in ["yes", "y", "true", "1"] else 0
    #             return 0

    #         helmet, vest, shoes = map(to_bit, (helmet, vest, shoes))

    #         # Create a new cursor for this operation
    #         # cursor = self.conn.cursor()
    #         cursor=self._get_cursor()
            
    #         cursor.execute("""
    #             INSERT INTO [PPE_DB].[dbo].[Notification_Details] (
    #                 Event_Id,
    #                 Camera_Id,
    #                 Camera_Name,
    #                 Image_Path,
    #                 Helmet,
    #                 Vest,
    #                 Shoes,
    #                 Event_Time,
    #                 Helmet_Color,
    #                 Ack_Message,
    #                 Ack_By,
    #                 Ack_Time,
    #                 Video_Path,
    #                 Email
    #             )
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', NULL, NULL, ?)
    #         """, (
    #             str(event_id_str),
    #             int(cam_id),
    #             camera_name,
    #             relative_image_path,
    #             helmet,
    #             vest,
    #             shoes,
    #             time,
    #             helmet_color,
    #             relative_video_path,
    #             1
    #         ))
            
    #         cursor.close()

    #     except Exception as e:
    #         self.logger.exception(f"Failed to insert notification: {e}")

    def insert_notification_if_allowed(
        self,
        event_id_str,
        cam_id,
        camera_name,
        relative_image_path,
        helmet,
        vest,
        shoes,
        time,
        helmet_color,
        relative_video_path,
        email=None
    ):
       pass


        # try:
        #     # def to_bit(value):
        #     #     if isinstance(value, (int, bool)):
        #     #         return int(value)
        #     #     if isinstance(value, str):
        #     #         return 1 if value.strip().lower() in ["yes", "y", "true", "1"] else 0
        #     #     return 0

        #     # helmet, vest, shoes = map(to_bit, (helmet, vest, shoes))
        #     helmet = 1 if (helmet[0] if isinstance(helmet, tuple) else helmet) == 'Yes' else 0
        #     vest   = 1 if (vest[0]   if isinstance(vest, tuple)   else vest)   == 'Yes' else 0
        #     shoes  = 1 if (shoes[0]  if isinstance(shoes, tuple)  else shoes)  == 'Yes' else 0
        #     if vest :

        #         cursor = self._get_cursor()
        #         email=1

        #         cursor.execute("""
        #             INSERT INTO [PPE_DB].[dbo].[Notification_Details] (
        #                 Event_Id,
        #                 Camera_Id,
        #                 Camera_Name,
        #                 Image_Path,
        #                 Helmet,
        #                 Vest,
        #                 Shoes,
        #                 Event_Time,
        #                 Helmet_Color,
        #                 Ack_Message,
        #                 Ack_By,
        #                 Ack_Time,
        #                 Video_Path,
        #                 Email
        #             )
        #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', NULL, NULL, ?, ?)
        #         """, (
        #             str(event_id_str),
        #             int(cam_id),
        #             camera_name,
        #             relative_image_path,
        #             helmet,
        #             vest,
        #             shoes,
        #             time,
        #             helmet_color,
        #             relative_video_path,
        #             email
        #         ))

        #         cursor.close()

        # except Exception as e:
        #     print(e)
        #     self.logger.exception(f"Failed to insert notification: {e}")


         
    def fetch_Camera_deatils(self):
        """
        Fetch camera details dynamically using FETCH_LIMIT from config.ini.
        """
        
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

            self.camera_roi_map = {}

            for row in rows:
                cam_id = int(row.CameraId)

                # Points stored as JSON string in DB
                pts = json.loads(row.Points)
        

                self.camera_roi_map[cam_id] = pts

            cursor.close()
            return self.camera_roi_map

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

            self.camera_ppe_policy = {}

            for cam_id, ppe_type, event in rows:
                cam_id = int(cam_id)
                ppe_type = ppe_type.strip().lower()

                # ensure dictionary for each cam_id
                if cam_id not in self.camera_ppe_policy:
                    self.camera_ppe_policy[cam_id] = {}

                # Logic for event-based allowance
                if ppe_type == "helmet" and str(event).strip() == "1":
                    self.camera_ppe_policy[cam_id][ppe_type] = 1
                elif ppe_type == "vest" and str(event).strip().lower() == "yes":
                    self.camera_ppe_policy[cam_id][ppe_type] = 1
                elif ppe_type not in ["helmet", "vest"]:
                    # for all other PPE types, store event as-is (optional)
                    self.camera_ppe_policy[cam_id][ppe_type] = int(event) if str(event).isdigit() else event

            return self.camera_ppe_policy

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
            self.helemt_color_not_allowed = [row[0] for row in rows] if rows else []
            return self.helemt_color_not_allowed
        
        except Exception as e:
            self.logger.exception(f"Failed to fetch restricted helmet colors: {e}")
            return []
    



    def fetch_last_event_ids(self):
        """
        Fetch the latest Event_Id and Id for each Camera_Id using ROW_NUMBER().
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT
                    Camera_Id,
                    Id AS Last_Updated_Id,
                    PARSENAME(REPLACE(Event_Id, '_', '.'), 1) AS Event_Number
                FROM (
                    SELECT
                        Camera_Id,
                        Id,
                        Event_Id,
                        ROW_NUMBER() OVER (PARTITION BY Camera_Id ORDER BY Id DESC) AS rn
                    FROM [PPE_DB].[dbo].[Event_Details]
                ) t
                WHERE rn = 1
                ORDER BY Camera_Id;
            """)

            rows = cursor.fetchall()
            cursor.close()

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

        except Exception as e:
            self.logger.exception("DB ERROR (Unified Video Path Update):")

       
    
   

    def fetch_Camera_name_deatils(self, n):
        """
        Return camera name from local cached map instead of DB query.
        If any exception occurs, safely return None.
        """
        try: 
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
            if helmet and vest and shoes:
                return 
            
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


def delete_old_folders(parent_path, safe_start_date, date_format="%Y-%m-%d"):
        """
        Deletes folders older than safe_start_date and returns count of deleted folders and files.
        """
        deleted_folders = 0
        deleted_files = 0

        for folder in Path(parent_path).iterdir():
            if not folder.is_dir():
                continue

            try:
                folder_date = datetime.strptime(folder.name, date_format)
            except ValueError:
                continue  # skip non-date folders

            # If folder date is older than the safe start date, delete
            if folder_date < safe_start_date:
                try:
                    file_count = sum(1 for _ in folder.rglob('*') if _.is_file())
                    shutil.rmtree(folder)
                    deleted_folders += 1
                    deleted_files += file_count
                except Exception as e:
                    print(f"⚠️ Could not delete folder {folder}: {e}")

        return deleted_folders, deleted_files
