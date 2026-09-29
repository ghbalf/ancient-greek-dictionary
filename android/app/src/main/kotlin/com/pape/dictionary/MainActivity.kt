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
        val versionFile = File(filesDir, "pape_dictionary.version")
        val installed = if (versionFile.exists()) versionFile.readText().trim() else ""
        if (dbFile.exists() && installed == DB_VERSION.toString()) return

        // Copy to a temp file first so an interrupted copy never leaves a truncated DB
        val tmpFile = File(filesDir, "pape_dictionary.db.tmp")
        assets.open("pape_dictionary.db").use { input ->
            tmpFile.outputStream().use { output ->
                input.copyTo(output)
            }
        }
        File(filesDir, "pape_dictionary.db-wal").delete()
        File(filesDir, "pape_dictionary.db-shm").delete()
        check(tmpFile.renameTo(dbFile)) { "Could not install dictionary database" }
        versionFile.writeText(DB_VERSION.toString())
    }

    companion object {
        // Bump whenever the bundled database changes (2 = FTS4 fulltext index)
        private const val DB_VERSION = 2
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
