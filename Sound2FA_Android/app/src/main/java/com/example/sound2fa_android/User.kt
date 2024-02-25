package com.example.sound2fa_android

class User {
    var username : String? = null
    var password : String? = null
    lateinit var token : String

    constructor(username : String, password : String, token : String){
        this.username = username
        this.password = password
        this.token = token
    }
}