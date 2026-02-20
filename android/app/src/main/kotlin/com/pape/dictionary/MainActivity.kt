package com.pape.dictionary

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import java.io.File

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        copyDatabaseIfNeeded()

        webView = WebView(this).apply {
            setupWebView(this)
        }
        setContentView(webView)

        webView.loadUrl("file:///android_asset/index.html")
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView(wv: WebView) {
        wv.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
        }
        wv.webViewClient = WebViewClient()

        val bridge = DictionaryBridge(this)
        wv.addJavascriptInterface(bridge, "Android")
    }

    private fun copyDatabaseIfNeeded() {
        val dbFile = File(filesDir, "pape_dictionary.db")
        if (dbFile.exists()) return

        assets.open("pape_dictionary.db").use { input ->
            dbFile.outputStream().use { output ->
                input.copyTo(output)
            }
        }
    }

    @Deprecated("Use OnBackPressedCallback", ReplaceWith("onBackPressedDispatcher"))
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            @Suppress("DEPRECATION")
            super.onBackPressed()
        }
    }
}
