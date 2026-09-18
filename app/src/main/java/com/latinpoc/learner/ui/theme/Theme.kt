package com.latinpoc.learner.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Light = lightColorScheme(
    primary = Umber,
    onPrimary = Parchment,
    primaryContainer = ChipLatin,
    onPrimaryContainer = UmberDark,
    secondary = Accent,
    onSecondary = Color.White,
    secondaryContainer = ChipPhonetic,
    onSecondaryContainer = Ink,
    background = Parchment,
    onBackground = Ink,
    surface = Color.White,
    onSurface = Ink,
    surfaceVariant = ParchmentDark,
    onSurfaceVariant = InkMuted
)

private val Dark = darkColorScheme(
    primary = Color(0xFFD4B896),
    onPrimary = UmberDark,
    primaryContainer = Umber,
    onPrimaryContainer = Parchment,
    secondary = Color(0xFFE0C56E),
    onSecondary = UmberDark,
    background = Color(0xFF161210),
    onBackground = Parchment,
    surface = Color(0xFF221A14),
    onSurface = Parchment
)

@Composable
fun LatinTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (darkTheme) Dark else Light, content = content)
}
