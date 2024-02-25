import time
import uuid
from html import unescape
from waitress import serve
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
import FCMManager
from audioAuth import audioAuth
from firebase_admin import storage, credentials, db
import firebase_admin
import os

mode = "prod"
privacy = False

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, name="storage")

app = Flask(__name__)
app.secret_key = 'super secret key'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    users_ref = db.reference(path='Users', url='https://sound2fa-default-rtdb.europe-west1.firebasedatabase.app/')
    user_data = users_ref.child(username).get()
    # user = users.get(username)

    if user_data and user_data.get('password') == password:
        # Render the audio recording page after successful login
        unique_key = str(uuid.uuid4())
        tokens = [user_data.get('token')]

        # print("Token: ", tokens)

        response = FCMManager.sendData(unique_key, tokens)
        if hasattr(response, 'error'):
            print('Failed to send message. Error:', response.error)
            return jsonify({'error': response.error})
        start_time = int(time.time() * 1000)
        print("Recording audio from devices..")
        return render_template('record_audio.html', username=username, unique_key=unique_key, tokens=tokens, time=start_time)
    else:
        flash('Invalid username or password. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    audio_file = request.files.get('audio')
    key = request.form["unique_key"]
    tokens = eval(unescape(request.form["tokens"]))

    path_pc = f'soundFiles/{request.form["username"]}_audioPC_{key}.wav'
    # Save the audio file to a specific location (you may want to handle this better)
    audio_file.save(path_pc)

    # Get the file named '{key}_audioAPP.aac' from firebase storage
    timeout_seconds = 6
    start_time = time.time()
    print("Trying to reach audio file from server..")
    while time.time() - start_time < timeout_seconds:
        try:
            # Initialize a storage client
            storage_client = storage.bucket('sound2fa.appspot.com')

            # Get a reference to the file in Firebase Storage
            blob = storage_client.blob(f'audio/{key}_audioAPP.wav')

            # Download the file to a local temporary location - we can delete this later
            path_app = f'soundFiles/{request.form["username"]}_audioAPP_{key}.wav'
            blob.download_to_filename(path_app)

            if blob.exists():
                print("Audio file found!")
                # path_pc = "C:/OzansStuff/Bitirme/Sounds/a_audioPC_bed00a3c-d236-40bc-85f6-cb4c832a7ec0.wav"
                # path_app = "C:/OzansStuff/Bitirme/Sounds/a_audioAPP_bed00a3c-d236-40bc-85f6-cb4c832a7ec0.wav"
                authenticated, too_quiet = audioAuth(path_pc, path_app)
                FCMManager.sendData(registration_token=tokens, notify_result=authenticated)
                if privacy:
                    try:
                        os.remove(path_pc)
                        os.remove(path_app)
                    except OSError as e:
                        print(f"Error removing file at {path_pc}: {e}")
                return jsonify({'message': 'Audio uploaded successfully', 'auth': authenticated, 'quiet': too_quiet})

        except Exception as e:
            # print(f"Exception caught: {e}")
            time.sleep(0.35)
        else:
            if privacy:
                try:
                    os.remove(path_pc)
                    os.remove(path_app)
                except OSError as e:
                    print(f"Error removing file at {path_pc}: {e}")
            print("Error retrieving file from Firebase Storage")
            return jsonify({'message': "Error retrieving file from Firebase Storage"})
    else:
        if privacy:
            try:
                os.remove(path_pc)
                os.remove(path_app)
            except OSError as e:
                print(f"Error removing file at {path_pc}: {e}")
        print("Error retrieving file from Firebase Storage")
        return jsonify({'message': "Error retrieving file from Firebase Storage"})


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/denied')
def denied():
    return render_template('denied.html')




if __name__ == '__main__':
    if mode == "dev":
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        serve(app, host="0.0.0.0", port=5000, threads=4)
