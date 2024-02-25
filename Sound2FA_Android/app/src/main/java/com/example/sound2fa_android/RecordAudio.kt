package com.example.sound2fa_android


import WavRecorder
import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.net.Uri
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.annotation.RequiresApi
import com.google.firebase.storage.FirebaseStorage
import com.google.firebase.storage.StorageReference
import java.io.DataOutputStream
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class RecordAudio {
    private var audioRecorder: WavRecorder? = null
    private var outputFile: String? = null

    @RequiresApi(Build.VERSION_CODES.S)
    fun startRecording(applicationContext: Context, handler: Handler, key: String?) {
        outputFile = getOutputMediaFile(applicationContext)?.absolutePath
        audioRecorder = WavRecorder(applicationContext)

        Log.d("RecordAudio: ","Output file: $outputFile")
        audioRecorder?.startRecording(outputFile ?: "")

        // Record for 4 seconds
        handler.postDelayed({
            audioRecorder?.stopRecording()
            sendAudioToServer(outputFile, key)
        }, 5000)
    }

    private fun getOutputMediaFile(applicationContext: Context): File? {
        val mediaStorageDir = File(
            applicationContext.getExternalFilesDir(null),
            "AudioRecordings"
        )

        if (!mediaStorageDir.exists()) {
            if (!mediaStorageDir.mkdirs()) {
                return null
            }
        }

        val timeStamp: String = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        Log.d("RecordAudio: ","Output file final: ${mediaStorageDir.path}${File.separator}AUD_$timeStamp.wav")
        return File("${mediaStorageDir.path}${File.separator}AUD_$timeStamp.wav")
    }

    private fun sendAudioToServer(filePath: String?, key: String?) {
        if (filePath != null) {
            val storage = FirebaseStorage.getInstance()
            val storageRef: StorageReference = storage.reference
            val audioRef: StorageReference = storageRef.child("audio/${key}_audioAPP.wav")

            val file = Uri.fromFile(File(filePath))
            val uploadTask = audioRef.putFile(file)

            uploadTask.addOnFailureListener {
                // Handle unsuccessful uploads
                Log.d("RecordAudio: ", "Upload failed.")

            }.addOnSuccessListener {
                // Task completed successfully
                Log.d("RecordAudio: ", "Upload success.")
            }

        } else {
            Log.d("RecordAudio: ", "File path is null.")
        }
    }
}
