package com.example.sound2fa_android

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.database.DatabaseReference
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.messaging.FirebaseMessaging

class MainActivity : AppCompatActivity() {
    private lateinit var database : DatabaseReference

    //Dummy user data for demonstration purposes
    private val users = mapOf(
        "ozan_colak" to mapOf("username" to "ozan_colak", "password" to "12345"),
        "gokhan_kaya" to mapOf("username" to "gokhan_kaya", "password" to "12345")
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        val editTextUsername = findViewById<EditText>(R.id.editTextUsername)
        val editTextPassword = findViewById<EditText>(R.id.editTextPassword)
        val buttonLogin = findViewById<Button>(R.id.buttonLogin)
        buttonLogin.setOnClickListener {
            // Retrieve username and password
            val username = editTextUsername.text.toString()
            val password = editTextPassword.text.toString()

            // Inside the onClick method of the login button click listener
            if (isValidCredentials(username, password)) {
                editTextUsername.text.clear()
                editTextPassword.text.clear()
                Toast.makeText(this, "Login Successful!", Toast.LENGTH_SHORT).show();
            } else {
                // Invalid credentials
                // Display an error message, for example, a toast.
                Toast.makeText(this, "Invalid Credentials!", Toast.LENGTH_SHORT).show();
            }
        }

        val buttonRegister = findViewById<Button>(R.id.buttonRegister)
        buttonRegister.setOnClickListener {
            // Retrieve username and password
            val username = editTextUsername.text.toString()
            val password = editTextPassword.text.toString()

            if (username.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Username or password cannot be empty", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }else if(username.length > 30 || password.length > 30){
                Toast.makeText(this, "Username or password is too long", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            database = FirebaseDatabase.getInstance("https://sound2fa-default-rtdb.europe-west1.firebasedatabase.app/").getReference("Users")

            FirebaseMessaging.getInstance().token.addOnSuccessListener { result ->
                if(result != null){
                    val user = User(username, password, result)
                    database.child(username).setValue(user).addOnSuccessListener {
                        editTextUsername.text.clear()
                        editTextPassword.text.clear()
                        Toast.makeText(this, "Registered successfully!", Toast.LENGTH_SHORT).show()
                    }.addOnFailureListener{
                        Toast.makeText(this, "Failed to register!", Toast.LENGTH_SHORT).show()

                    }
                }
            }
        }

    }

    private fun isValidCredentials(username: String, password: String): Boolean {
        val user = users[username]

        if(user?.get("username").equals(username) && user?.get("password").equals(password)){
            return true
        }
        else
            return false
    }

}