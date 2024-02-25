import firebase_admin
from firebase_admin import credentials, messaging
from flask import jsonify

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)


# @app.route('/api/sendRecordRequest', methods=['POST'])
def sendData(unique_key=None, registration_token=None, notify_result=None):
    try:
        # Get data from the request
        # data = request.get_json()

        # Extract numbers from the request data
        # title = data['title']
        # msg = data['msg']
        if registration_token is None: #default phone
            registration_token = [
                "fUaAxkPMRu-xgfwNeYNGUa:APA91bHRudKaH7nFF8Ez0v3EFM-aFhFKESI2w10q0Gn4v-NCFlAEWs_oPqU"
                "-283e0JZL8ln1gjQLJqa3FgkDF6PSDM3RJa_qeLEsUjV_9VV1JSzYc0jtBkVdKtmthhH7ytvEpHgPbXdR"]

        if notify_result is None:
            dataObject = {
                "command": "recordAudio",
                "key": unique_key
            }
            # dataObject = data['dataObject']
            # tokens = data['tokens']
            title = "Request"
            body = "Authentication request has been received!"

        else:
            dataObject = None
            title = "Authentication Notify"
            if notify_result:
                body = "The user has been authenticated!"
            else:
                body = "The user trying to login has been declined!"

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=dataObject,
            tokens=registration_token,
        )

        response = messaging.send_each_for_multicast(message)
        # Check if the response has an 'error' attribute
        if hasattr(response, 'error'):
            print('Failed to send message. Error:', response.error)
            return jsonify({'error': response.error})

        # If no error, assume success
        message_ids = [entry.message_id for entry in response.responses]
        print('Successfully sent messages. Message IDs:', message_ids)
        returned = {'success': 'Successfully sent messages.', 'message_ids': message_ids}
        return jsonify(returned)

    except Exception as e:
        # Handle errors
        error_message = {'error': str(e)}
        return jsonify(error_message), 400
