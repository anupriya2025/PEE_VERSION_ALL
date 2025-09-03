import pyodbc
import time
from datetime import datetime


class CameraDatabase:
    def __init__(self):
        # ✅ Connect to SQL Server
        self.conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=ITDT14;'
            'DATABASE=PPE_DB_NEW;'
            'UID=sa;'
            'PWD=root1234'
        )
        self.cursor = self.conn.cursor()

    # ==========================
    # CAMERA FUNCTIONS
    # ==========================
    def fetch_all_cameras(self, limit=1000):
        """Fetch all cameras up to limit."""
        try:
            self.cursor.execute(f"""
                SELECT TOP {limit} 
                    Camera_name, 
                    Camera_direction, 
                    URL
                FROM [PPE_DB_NEW].[dbo].[Camera_Details]
                ORDER BY Camera_name ASC
            """)
            rows = self.cursor.fetchall()
            return [tuple(row) for row in rows]
        except Exception as e:
            print(f"❌ Failed to fetch cameras: {e}")
            return []

    def add_camera(self, camera_name, camera_direction, url):
        """Add new camera."""
        try:
            self.cursor.execute("""
                INSERT INTO [PPE_DB_NEW].[dbo].[Camera_Details] 
                (Camera_name, Camera_direction, URL)
                VALUES (?, ?, ?)
            """, (camera_name, camera_direction, url))
            self.conn.commit()
            print(f"✅ Camera '{camera_name}' added successfully.")
        except Exception as e:
            print(f"❌ Failed to add camera: {e}")

    def update_camera(self, camera_name, new_direction=None, new_url=None):
        print("Update camera details.************************************")
        try:
            if new_direction and new_url:
                self.cursor.execute("""
                    UPDATE [PPE_DB_NEW].[dbo].[Camera_Details]
                    SET Camera_direction = ?, URL = ?
                    WHERE Camera_name = ?
                """, (new_direction, new_url, camera_name))
            elif new_direction:
                self.cursor.execute("""
                    UPDATE [PPE_DB_NEW].[dbo].[Camera_Details]
                    SET Camera_direction = ?
                    WHERE Camera_name = ?
                """, (new_direction, camera_name))
            elif new_url:
                self.cursor.execute("""
                    UPDATE [PPE_DB_NEW].[dbo].[Camera_Details]
                    SET URL = ?
                    WHERE Camera_name = ?
                """, (new_url, camera_name))
            else:
                print("⚠️ Nothing to update.")
                return
            self.conn.commit()
            print(f"✅ Camera '{camera_name}' updated successfully.")
        except Exception as e:
            print(f"❌ Failed to update camera: {e}")

    def delete_camera(self, camera_name):
        """Delete a camera by name."""
        try:
            self.cursor.execute("""
                DELETE FROM [PPE_DB_NEW].[dbo].[Camera_Details]
                WHERE Camera_name = ?
            """, (camera_name,))
            self.conn.commit()
            print(f"✅ Camera '{camera_name}' deleted successfully.")
        except Exception as e:
            print(f"❌ Failed to delete camera: {e}")

    def close(self):
        """Close DB connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            print("✅ Camera DB connection closed.")
        except Exception as e:
            print(f"❌ Failed to close DB: {e}")
