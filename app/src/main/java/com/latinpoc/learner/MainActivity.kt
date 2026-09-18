package com.latinpoc.learner

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.latinpoc.learner.navigation.LatinNavGraph
import com.latinpoc.learner.ui.theme.LatinTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            LatinTheme {
                Surface(Modifier.fillMaxSize()) { LatinNavGraph() }
            }
        }
    }
}
