import argparse
import json
import sqlite3
import uuid

def main(args):
    # Read the contents of the form_parts JSON file
    with open(args.form_parts_path, 'r') as file:
        form_parts_json = file.read()

    # Validate JSON format
    try:
        form_parts = json.loads(form_parts_json)
    except json.JSONDecodeError:
        print("Error: The form_parts JSON is not valid.")
        return

    # Read the contents of the base64-encoded PNG URI file
    with open(args.base64_png_path, 'r') as file:
        base64_png_uri = file.read()

    # Connect to the SQLite database
    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()

    # Generate a UUID for the new row
    new_id = str(uuid.uuid4())

    # Insert the new CharsheetType row into the database
    try:
        cursor.execute("""
            INSERT INTO charsheet_type (id, name, form_parts, b64_img)
            VALUES (?, ?, ?, ?);
        """, (new_id, args.type_name, json.dumps(form_parts), base64_png_uri))
        conn.commit()
        print("Row inserted successfully.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert a new CharsheetType row into the SQLite database.')
    parser.add_argument('type_name', help='The name of the charsheet type.')
    parser.add_argument('form_parts_path', help='Path to the text file containing the form_parts JSON.')
    parser.add_argument('base64_png_path', help='Path to the text file containing the base64-encoded PNG URI.')
    parser.add_argument('db_path', help='Path to the SQLite database file.')

    args = parser.parse_args()
    main(args)
