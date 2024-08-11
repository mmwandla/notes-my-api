from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import json
import base64

app = Flask(__name__)

# Decode the Firebase service account key from the environment variable
firebase_service_account_key = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')
if firebase_service_account_key:
    service_account_info = json.loads(base64.b64decode(firebase_service_account_key))
else:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set")

# Initialize Firebase Admin SDK with a manually set database URL
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://notes-app777-default-rtdb.firebaseio.com'  # Manually set database URL
})


# Helper function to convert a note from Firebase format to Python dict
def note_to_dict(note):
    note_dict = note.val()
    note_dict['id'] = note.key
    return note_dict


@app.route('/api/notes', methods=['GET'])
def get_notes():
    user_id = request.args.get('userId')
    if user_id:
        notes_ref = db.reference('notes')
        notes = notes_ref.order_by_child('userId').equal_to(user_id).get()
        return jsonify([note_to_dict(note) for note in notes.items()]) if notes else jsonify([])
    return jsonify({"error": "userId parameter is required"}), 400


@app.route('/api/notes/<id>', methods=['GET'])
def get_note(id):
    note_ref = db.reference(f'notes/{id}')
    note = note_ref.get()
    if note:
        note['id'] = id
        return jsonify(note)
    return jsonify({"error": "Note not found"}), 404


@app.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json
    new_note_ref = db.reference('notes').push({
        'userId': data.get('userId'),
        'title': data.get('title'),
        'content': data.get('content'),
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    })
    return jsonify({**data, 'id': new_note_ref.key}), 201


@app.route('/api/notes/<id>', methods=['PUT'])
def update_note(id):
    data = request.json
    note_ref = db.reference(f'notes/{id}')
    note = note_ref.get()
    if note:
        note_ref.update({
            'title': data.get('title', note['title']),
            'content': data.get('content', note['content']),
            'updatedAt': datetime.utcnow().isoformat()
        })
        return jsonify({**note, 'id': id})
    return jsonify({"error": "Note not found"}), 404


@app.route('/api/notes/<id>', methods=['DELETE'])
def delete_note(id):
    note_ref = db.reference(f'notes/{id}')
    if note_ref.get():
        note_ref.delete()
        return '', 204
    return jsonify({"error": "Note not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
