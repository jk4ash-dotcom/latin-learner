package com.latinpoc.learner.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.latinpoc.learner.BuildConfig
import com.latinpoc.learner.data.CatalogTotals

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AboutScreen(
    version: String,
    scope: String,
    totals: CatalogTotals,
    onBack: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("About") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .navigationBarsPadding()
                .verticalScroll(rememberScrollState())
                .padding(24.dp)
        ) {
            Text("Latin Learner", style = MaterialTheme.typography.headlineSmall)
            Spacer(Modifier.height(8.dp))
            Text(
                "Offline Latin Bible learner POC. Scope: ${scope.ifBlank { "Genesis" }}. " +
                    "${totals.books} books · ${totals.verses} verses · ${totals.glosses} gloss entries.",
                style = MaterialTheme.typography.bodyLarge
            )
            Spacer(Modifier.height(12.dp))
            Text(
                "This is an independent proof-of-concept — not an official Church product.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(Modifier.height(16.dp))
            Text("Latin text", style = MaterialTheme.typography.titleMedium)
            Text(
                "Latin text: Clementine Vulgate (PD; Clementine Vulgate Project / Michael Tweedale).",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            Text("English underlay", style = MaterialTheme.typography.titleMedium)
            Text(
                "Douay–Rheims Challoner (Public Domain). Verse-level only — not word-aligned.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            Text("Phonetics", style = MaterialTheme.typography.titleMedium)
            Text(
                "Ecclesiastical (Italianate) scheme v1 — documented in docs/SOURCES.md. " +
                    "Classical pronunciation toggle is future work. Scriba accuracy-gates vocalizations.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            Text("Glosses", style = MaterialTheme.typography.titleMedium)
            Text(
                "Whitaker’s WORDS (William A. Whitaker) — permissive licence. " +
                    "UI: “Possible sense(s)” — Gloss ≠ verse translation. Stubs marked for Scriba.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            Text("Licenses", style = MaterialTheme.typography.titleMedium)
            Text(
                "Clementine Vulgate (PD) · Douay–Rheims Challoner (PD) · Whitaker WORDS (permissive).",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            Text("Security", style = MaterialTheme.typography.titleMedium)
            Text(
                "No INTERNET permission. Offline assets only. Argus: emoji2 kept on classpath; " +
                    "EmojiCompatInitializer removed; allowBackup=false.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(24.dp))
            Text(
                "App ${BuildConfig.VERSION_NAME} (${BuildConfig.GIT_SHA}) · pack $version · ${BuildConfig.APPLICATION_ID}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
