package com.example.photouploader

import android.Manifest
import android.content.ContentValues
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.util.Base64
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.concurrent.TimeUnit
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.lifecycleScope

class MainActivity : ComponentActivity() {
    private var imageUri: Uri? = null
    private lateinit var cameraPermissionLauncher: ActivityResultLauncher<String>
    private lateinit var takePictureLauncher: ActivityResultLauncher<Uri>
    private val serverUrl = "http://10.18.46.31:5000/upload"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Registrar el launcher para solicitar permisos de cámara
        cameraPermissionLauncher = registerForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { isGranted ->
            if (isGranted) {
                startCamera()
            } else {
                Toast.makeText(
                    this,
                    "Se necesita permiso de cámara para esta función",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }

        // Registrar el launcher para tomar fotos
        takePictureLauncher = registerForActivityResult(
            ActivityResultContracts.TakePicture()
        ) { success ->
            if (success) {
                setContent {
                    AppScreen(
                        imageUri = imageUri,
                        onCaptureClick = { checkCameraPermission() },
                        onUploadClick = { uploadImage() }
                    )
                }
            }
        }

        setContent {
            AppScreen(
                imageUri = imageUri,
                onCaptureClick = { checkCameraPermission() },
                onUploadClick = { uploadImage() }
            )
        }
    }

    private fun checkCameraPermission() {
        when {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED -> {
                startCamera()
            }
            else -> {
                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
            }
        }
    }

    private fun startCamera() {
        val contentValues = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, "img_${System.currentTimeMillis()}")
            put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
        }

        imageUri = contentResolver.insert(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            contentValues
        )

        imageUri?.let { uri ->
            takePictureLauncher.launch(uri)
        } ?: run {
            Toast.makeText(this, "Error al crear el archivo para la imagen", Toast.LENGTH_SHORT).show()
        }
    }

    private fun uploadImage() {
        val uri = imageUri ?: run {
            Toast.makeText(this, "Primero debes tomar una foto", Toast.LENGTH_SHORT).show()
            return
        }

        lifecycleScope.launch {
            try {
                val base64Image = uriToBase64(uri)
                val jsonObject = JSONObject()
                jsonObject.put("image", base64Image)

                val requestBody = jsonObject.toString()
                    .toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())

                val request = Request.Builder()
                    .url(serverUrl)
                    .post(requestBody)
                    .build()

                val client = OkHttpClient.Builder()
                    .connectTimeout(30, TimeUnit.SECONDS)
                    .writeTimeout(30, TimeUnit.SECONDS)
                    .readTimeout(30, TimeUnit.SECONDS)
                    .build()

                withContext(Dispatchers.IO) {
                    try {
                        val response = client.newCall(request).execute()
                        if (response.isSuccessful) {
                            withContext(Dispatchers.Main) {
                                Toast.makeText(
                                    this@MainActivity,
                                    "Imagen subida correctamente",
                                    Toast.LENGTH_SHORT
                                ).show()
                            }
                        } else {
                            withContext(Dispatchers.Main) {
                                Toast.makeText(
                                    this@MainActivity,
                                    "Error en el servidor: ${response.code}",
                                    Toast.LENGTH_LONG
                                ).show()
                            }
                        }
                    } catch (e: IOException) {
                        withContext(Dispatchers.Main) {
                            Toast.makeText(
                                this@MainActivity,
                                "Error al enviar: ${e.message}",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@MainActivity,
                    "Error al procesar la imagen: ${e.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    private suspend fun uriToBase64(uri: Uri): String {
        return withContext(Dispatchers.IO) {
            val inputStream = contentResolver.openInputStream(uri)
            val bitmap = BitmapFactory.decodeStream(inputStream)
            val outputStream = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 100, outputStream)
            val byteArray = outputStream.toByteArray()
            Base64.encodeToString(byteArray, Base64.DEFAULT)
        }
    }
}

@Composable
fun AppScreen(
    imageUri: Uri?,
    onCaptureClick: () -> Unit,
    onUploadClick: () -> Unit
) {
    val context = LocalContext.current
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(bottom = 16.dp)
            ) {
                if (imageUri != null) {
                    val bitmap by remember(imageUri) {
                        mutableStateOf(
                            try {
                                context.contentResolver.openInputStream(imageUri)?.use {
                                    BitmapFactory.decodeStream(it)
                                }
                            } catch (e: Exception) {
                                null
                            }
                        )
                    }
                    bitmap?.let {
                        Image(
                            bitmap = it.asImageBitmap(),
                            contentDescription = "Imagen capturada",
                            contentScale = ContentScale.Fit,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                } else {
                    // Placeholder para cuando no hay imagen
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text("No hay imagen")
                        }
                    }
                }
            }

            Button(
                onClick = onCaptureClick,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Tomar Foto")
            }

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = onUploadClick,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Enviar al Servidor")
            }
        }
    }
}