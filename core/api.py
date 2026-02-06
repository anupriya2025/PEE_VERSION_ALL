from flask import Flask, jsonify


def create_api(db_path="./resource/events.db", obj_db=None):
    app = Flask(__name__)
    db = obj_db

    @app.route("/latest-event", methods=["GET"])
    def get_latest_event():
        db.cursor.execute("""
            SELECT timestamp, event_id, camera_name, image_base64
            FROM events
            ORDER BY id DESC
            LIMIT 1
        """)
        row = db.cursor.fetchone()
        if row:
            return jsonify({
                "timestamp": row[0],
                "event_id": row[1],
                "camera_name": row[2],
                "image_base64": row[3]
            })
        return jsonify({"message": "No events found"}), 404

    @app.route("/events/<int:count>", methods=["GET"])
    def get_last_n_events(count):
        db.cursor.execute(f"""
               SELECT timestamp, event_id, camera_name, image_base64
               FROM events
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
