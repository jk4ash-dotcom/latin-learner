package com.latinpoc.learner.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.latinpoc.learner.data.BookTitles
import com.latinpoc.learner.data.Gloss
import com.latinpoc.learner.data.GlossDisplay
import com.latinpoc.learner.data.Token
import com.latinpoc.learner.data.Verse
import com.latinpoc.learner.ui.theme.ChipLatin
import com.latinpoc.learner.ui.theme.ChipPhonetic
import com.latinpoc.learner.ui.theme.Ink

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VerseScreen(
    verse: Verse,
    resolveGloss: (String?) -> Gloss?,
    onBack: () -> Unit
) {
    var selected by remember { mutableStateOf<Token?>(null) }
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val title = BookTitles.verseLabel(verse.book, verse.chapter, verse.verse)
    val tokens = GlossDisplay.displayTokens(verse)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(title) },
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
                .padding(16.dp)
        ) {
            Text(
                "Latin + ecclesiastical phonetic (paired chips)",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(8.dp))
            Row(
                Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.Top
            ) {
                tokens.forEach { token ->
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.widthIn(min = 72.dp)
                    ) {
                        AssistChip(
                            onClick = { selected = token },
                            modifier = Modifier.heightIn(min = 40.dp),
                            label = {
                                Text(
                                    text = token.la,
                                    color = Ink,
                                    fontSize = 18.sp,
                                    lineHeight = 24.sp,
                                    textAlign = TextAlign.Center,
                                    softWrap = false,
                                    overflow = TextOverflow.Visible,
                                    maxLines = 1
                                )
                            },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = ChipLatin,
                                labelColor = Ink
                            )
                        )
                        AssistChip(
                            onClick = { selected = token },
                            label = {
                                Text(
                                    token.phonetic,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = Ink,
                                    textAlign = TextAlign.Center
                                )
                            },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = ChipPhonetic,
                                labelColor = Ink
                            )
                        )
                    }
                }
            }
            Spacer(Modifier.height(20.dp))
            HorizontalDivider()
            Spacer(Modifier.height(16.dp))
            Text(
                "Douay–Rheims (verse)",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(6.dp))
            Text(verse.english.text, style = MaterialTheme.typography.bodyLarge)
            Text(
                "${verse.english.source} · ${verse.english.license}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 6.dp)
            )
            Spacer(Modifier.height(12.dp))
            Text(
                "Tap a chip for possible sense(s). Gloss ≠ verse translation.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }

    val token = selected
    if (token != null) {
        val shown = GlossDisplay.forToken(token, resolveGloss(token.glossId))
        ModalBottomSheet(onDismissRequest = { selected = null }, sheetState = sheetState) {
            Column(
                Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 24.dp, vertical = 8.dp)
            ) {
                Text("Possible sense(s)", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(8.dp))
                Text(token.la, style = MaterialTheme.typography.titleLarge, color = Ink)
                Text(
                    token.phonetic + if (token.phoneticPending) " · pending Scriba" else "",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 2.dp)
                )
                token.lemmaId?.let {
                    Text(
                        "Key $it · ${token.phoneticScheme}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Spacer(Modifier.height(12.dp))
                Text(shown.primary, style = MaterialTheme.typography.titleMedium)
                shown.senses.forEach { s ->
                    Text("• $s", style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(top = 4.dp))
                }
                shown.policyNote?.let { note ->
                    Text(
                        note,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 6.dp)
                    )
                }
                shown.definition?.let { def ->
                    Spacer(Modifier.height(8.dp))
                    Text(def, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (shown.source.isNotBlank()) {
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Source: ${shown.source}",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Spacer(Modifier.height(16.dp))
                Text(
                    "Gloss ≠ verse translation",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.secondary
                )
                Spacer(Modifier.height(24.dp))
            }
        }
    }
}
