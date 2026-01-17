package com.salvavidas.audioclient

import android.Manifest
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import okhttp3.*
import okio.ByteString
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Salvavidas Android Audio Client
 * Ultra low-latency audio capture and streaming to Salvavidas server
 *
 * This app is a SERVANT - it only captures and sends audio, no processing
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "SalvavidasAudio"
        private const val REQUEST_RECORD_AUDIO_PERMISSION = 200

        // Audio Configuration - optimized for low latency speech
        private const val SAMPLE_RATE = 16000  // 16kHz
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
        private const val BUFFER_SIZE_MULTIPLIER = 2

        // Streaming Configuration
        private const val CHUNK_SIZE = 1024  // Samples per chunk
        private const val DEFAULT_SERVER_URL = "ws://192.168.1.100:8000/ws"
    }

    // Permissions
    private val permissions = arrayOf(Manifest.permission.RECORD_AUDIO)
    private var permissionToRecordAccepted = false

    // UI Components
    private lateinit var serverUrlInput: EditText
    private lateinit var connectButton: Button
    private lateinit var startButton: Button
    private lateinit var stopButton: Button
    private lateinit var statusText: TextView
    private lateinit var statsText: TextView

    // Audio
    private var audioRecord: AudioRecord? = null
    private var bufferSize: Int = 0
    private var isRecording = false

    // WebSocket
    private var webSocket: WebSocket? = null
    private var isConnected = false

    // Coroutines
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var captureJob: Job? = null

    // Statistics
    private var packetsSent = 0L
    private var bytessent = 0L
    private var startTime = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize UI
        initializeUI()

        // Request permissions
        requestPermissions()

        // Calculate buffer size
        bufferSize = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            CHANNEL_CONFIG,
            AUDIO_FORMAT
        ) * BUFFER_SIZE_MULTIPLIER

        Log.d(TAG, "Buffer size: $bufferSize bytes")
    }

    private fun initializeUI() {
        serverUrlInput = findViewById(R.id.serverUrlInput)
        connectButton = findViewById(R.id.connectButton)
        startButton = findViewById(R.id.startButton)
        stopButton = findViewById(R.id.stopButton)
        statusText = findViewById(R.id.statusText)
        statsText = findViewById(R.id.statsText)

        serverUrlInput.setText(DEFAULT_SERVER_URL)

        connectButton.setOnClickListener { toggleConnection() }
        startButton.setOnClickListener { startStreaming() }
        stopButton.setOnClickListener { stopStreaming() }

        updateUI()
    }

    private fun requestPermissions() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(this, permissions, REQUEST_RECORD_AUDIO_PERMISSION)
        } else {
            permissionToRecordAccepted = true
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        permissionToRecordAccepted = if (requestCode == REQUEST_RECORD_AUDIO_PERMISSION) {
            grantResults[0] == PackageManager.PERMISSION_GRANTED
        } else {
            false
        }

        if (!permissionToRecordAccepted) {
            Toast.makeText(this, "Microphone permission required!", Toast.LENGTH_LONG).show()
            finish()
        }
    }

    private fun toggleConnection() {
        if (isConnected) {
            disconnect()
        } else {
            connect()
        }
    }

    private fun connect() {
        val serverUrl = serverUrlInput.text.toString()

        if (serverUrl.isBlank()) {
            Toast.makeText(this, "Please enter server URL", Toast.LENGTH_SHORT).show()
            return
        }

        updateStatus("Connecting to $serverUrl...")

        val client = OkHttpClient()
        val request = Request.Builder()
            .url(serverUrl)
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d(TAG, "WebSocket connected")
                isConnected = true

                runOnUiThread {
                    updateStatus("✓ Connected to server")
                    updateUI()
                }

                // Send ready signal
                val readyMessage = """{"type":"client_ready","device":"Android"}"""
                webSocket.send(readyMessage)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.d(TAG, "Received: $text")
                // Handle server responses (transcriptions, translations, etc.)
                runOnUiThread {
                    updateStatus("Received: ${text.take(50)}...")
                }
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                Log.d(TAG, "Received binary: ${bytes.size()} bytes")
                // Handle binary data from server (TTS audio, etc.)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closing: $code / $reason")
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closed: $code / $reason")
                isConnected = false

                runOnUiThread {
                    updateStatus("✗ Disconnected")
                    updateUI()
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "WebSocket error: ${t.message}", t)
                isConnected = false

                runOnUiThread {
                    updateStatus("✗ Connection failed: ${t.message}")
                    updateUI()
                }
            }
        })
    }

    private fun disconnect() {
        stopStreaming()

        webSocket?.close(1000, "User disconnect")
        webSocket = null
        isConnected = false

        updateStatus("Disconnected")
        updateUI()
    }

    private fun startStreaming() {
        if (!permissionToRecordAccepted) {
            Toast.makeText(this, "Microphone permission required!", Toast.LENGTH_SHORT).show()
            return
        }

        if (!isConnected) {
            Toast.makeText(this, "Please connect to server first", Toast.LENGTH_SHORT).show()
            return
        }

        if (isRecording) {
            Toast.makeText(this, "Already recording", Toast.LENGTH_SHORT).show()
            return
        }

        // Initialize AudioRecord
        try {
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.VOICE_COMMUNICATION,  // Optimized for voice
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize
            )

            if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                Toast.makeText(this, "Failed to initialize AudioRecord", Toast.LENGTH_SHORT).show()
                audioRecord = null
                return
            }

            audioRecord?.startRecording()
            isRecording = true

            // Reset statistics
            packetsSent = 0
            bytesSent = 0
            startTime = System.currentTimeMillis()

            updateStatus("🎤 Recording and streaming...")
            updateUI()

            // Start capture and stream coroutine
            captureJob = scope.launch(Dispatchers.IO) {
                captureAndStreamAudio()
            }

        } catch (e: SecurityException) {
            Log.e(TAG, "Security exception: ${e.message}", e)
            Toast.makeText(this, "Microphone access denied", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Log.e(TAG, "Error starting recording: ${e.message}", e)
            Toast.makeText(this, "Failed to start recording", Toast.LENGTH_SHORT).show()
        }
    }

    private fun stopStreaming() {
        if (!isRecording) return

        isRecording = false
        captureJob?.cancel()

        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null

        updateStatus("✓ Stopped")
        updateUI()
    }

    private suspend fun captureAndStreamAudio() {
        val audioBuffer = ShortArray(CHUNK_SIZE)

        while (isRecording && isConnected) {
            // Read from microphone
            val samplesRead = audioRecord?.read(audioBuffer, 0, CHUNK_SIZE) ?: 0

            if (samplesRead > 0) {
                // Convert to bytes (little-endian PCM16)
                val byteBuffer = ByteBuffer.allocate(samplesRead * 2)
                byteBuffer.order(ByteOrder.LITTLE_ENDIAN)

                for (i in 0 until samplesRead) {
                    var sample = audioBuffer[i]

                    // Simple noise gate (-40dB)
                    if (Math.abs(sample.toInt()) < 200) {
                        sample = 0
                    }

                    byteBuffer.putShort(sample)
                }

                // Send via WebSocket
                val bytes = byteBuffer.array()
                webSocket?.send(ByteString.of(*bytes))

                packetsSent++
                bytesSent += bytes.size

                // Update stats every second
                if (packetsSent % 10 == 0L) {
                    withContext(Dispatchers.Main) {
                        updateStats()
                    }
                }
            }

            // Small delay to prevent CPU overload
            delay(10)
        }
    }

    private fun updateStatus(status: String) {
        statusText.text = status
        Log.d(TAG, "Status: $status")
    }

    private fun updateStats() {
        val elapsed = (System.currentTimeMillis() - startTime) / 1000.0
        val packetsPerSec = if (elapsed > 0) packetsSent / elapsed else 0.0
        val kbps = if (elapsed > 0) (bytesSent * 8) / (elapsed * 1000) else 0.0

        val stats = """
            Packets sent: $packetsSent
            Data sent: ${bytesSent / 1024} KB
            Rate: ${"%.1f".format(packetsPerSec)} pkt/s
            Bitrate: ${"%.1f".format(kbps)} kbps
            Duration: ${elapsed.toInt()}s
        """.trimIndent()

        statsText.text = stats
    }

    private fun updateUI() {
        connectButton.text = if (isConnected) "Disconnect" else "Connect"
        connectButton.isEnabled = true

        serverUrlInput.isEnabled = !isConnected

        startButton.isEnabled = isConnected && !isRecording
        stopButton.isEnabled = isRecording
    }

    override fun onDestroy() {
        super.onDestroy()
        stopStreaming()
        disconnect()
        scope.cancel()
    }
}
