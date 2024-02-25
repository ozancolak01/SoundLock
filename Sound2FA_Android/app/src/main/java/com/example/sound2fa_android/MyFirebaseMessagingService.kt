package com.example.sound2fa_android

import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.annotation.RequiresApi
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import android.app.AlertDialog
import android.content.Context

class MyFirebaseMessagingService : FirebaseMessagingService(){
companion object{
    const val TAG = "PUSH_Android"
}

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d(TAG, "token: $token")
    }

    @RequiresApi(Build.VERSION_CODES.S)
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        // ...

        // TODO(developer): Handle FCM messages here.
        // Not getting messages here? See why this may be: https://goo.gl/39bRNJ
        Log.d(TAG, "From: ${remoteMessage.from}")

        // Check if message contains a data payload.
        if (remoteMessage.data.isNotEmpty()) {
            Log.d(TAG, "Message data payload: ${remoteMessage.data}")

            if(remoteMessage.data["command"] == "recordAudio"){
                val recordAudio = RecordAudio()
                recordAudio.startRecording(applicationContext, handler, remoteMessage.data["key"])
            }
        }

        // Check if message contains a notification payload.
        remoteMessage.notification?.let {
            Log.d(TAG, "Message Notification Body: ${it.body}")
            showOnScreen(it.body)
        }

        // Also if you intend on generating your own notifications as a result of a received FCM
        // message, here is where that should be initiated. See sendNotification method below.
    }

    private val handler = Handler(Looper.getMainLooper())

    private fun showOnScreen(message: String?) {
        handler.post {
            message?.let {
                    Toast.makeText(applicationContext, it, Toast.LENGTH_SHORT).show()
            }
        }
    }

}