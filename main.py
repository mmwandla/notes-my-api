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


def note_to_dict(note, note_id):
    note_dict = note
    note_dict['id'] = note_id
    return note_dict


@app.route('/api/notes', methods=['GET'])
def get_notes():
    user_id = request.args.get('userId')
    if user_id:
        notes_ref = db.reference(f'users/{user_id}/notes')
        notes = notes_ref.get()
        if notes:
            return jsonify([note_to_dict(note, note_id) for note_id, note in notes.items()])
        return jsonify([])
    return jsonify({"error": "userId parameter is required"}), 400


@app.route('/api/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    user_id = request.args.get('userId')
    if user_id:
        note_ref = db.reference(f'users/{user_id}/notes/{note_id}')
        note = note_ref.get()
        if note:
            note['id'] = note_id
            return jsonify(note)
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"error": "userId parameter is required"}), 400


@app.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json
    user_id = data.get('userId')
    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    note_data = {
        'userId': user_id,
        'title': data.get('title'),
        'content': data.get('content'),
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }

    new_note_ref = db.reference(f'users/{user_id}/notes').push(note_data)
    note_data['id'] = new_note_ref.key
    return jsonify(note_data), 201


@app.route('/api/notes/<user_id>/<note_id>', methods=['PUT'])
def update_note(user_id, note_id):
    data = request.json
    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    note_ref = db.reference(f'users/{user_id}/notes/{note_id}')
    note = note_ref.get()
    if note:
        note_ref.update({
            'title': data.get('title', note['title']),
            'content': data.get('content', note['content']),
            'updatedAt': datetime.utcnow().isoformat()
        })
        return jsonify({**note, 'id': note_id})
    return jsonify({"error": "Note not found"}), 404



@app.route('/api/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    user_id = request.args.get('userId')
    if user_id:
        note_ref = db.reference(f'users/{user_id}/notes/{note_id}')
        if note_ref.get():
            note_ref.delete()
            return '', 204
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"error": "userId parameter is required"}), 400


if __name__ == '__main__':
    app.run(debug=True)
