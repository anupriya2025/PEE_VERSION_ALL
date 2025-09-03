from flask import Flask, jsonify
from core.database import EventDatabase

def create_api(db_path="./resource/events_new.db"):
    app = Flask(__name__)
    db = EventDatabase(db_path)

    @app.route("/latest-event", methods=["GET"])
    def get_latest_event():
        db.cursor.execute("""
            SELECT  ID, camera_name, image_base64
            FROM events_new
            ORDER BY id DESC
            LIMIT 1
        """)
        row = db.cursor.fetchone()
        if row:
            return jsonify({
                "event_id": row[0],
                "camera_name": row[1],
                "image_base64": row[2]
            })
        return jsonify({"message": "No events found"}), 404

    @app.route("/events/<int:count>", methods=["GET"])
    def get_last_n_events(count):
        db.cursor.execute(f"""
               SELECT timestamp, event_id, camera_name, image_base64
               FROM events_new
               ORDER BY id DESC
               LIMIT ?
           """, (count,))
        rows = db.cursor.fetchall()

        if rows:
            results = [
                {
                    "timestamp": row[0],
                    "event_id": row[1],
                    "camera_name": row[2],
                    "image_base64": row[3]
                }
                for row in rows
            ]
            return jsonify(results), 200
        return jsonify({"message": "No events found"}), 404

    return app
