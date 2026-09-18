package com.latinpoc.learner.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.latinpoc.learner.LatinApp
import com.latinpoc.learner.data.BookTitles
import com.latinpoc.learner.data.ChapterIndex
import com.latinpoc.learner.ui.screens.AboutScreen
import com.latinpoc.learner.ui.screens.BookScreen
import com.latinpoc.learner.ui.screens.ChapterScreen
import com.latinpoc.learner.ui.screens.HomeScreen
import com.latinpoc.learner.ui.screens.VerseScreen

@Composable
fun LatinNavGraph() {
    val navController = rememberNavController()
    val app = LatinApp.from(LocalContext.current)
    val repo by app.repository.collectAsStateWithLifecycle()
    val loadError by app.loadError.collectAsStateWithLifecycle()

    val ready = repo
    if (ready == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(24.dp)) {
                if (loadError != null) {
                    Text("Could not load catalog", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Text(
                        loadError ?: "",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                } else {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(16.dp))
                    Text("Loading Latin catalog…", style = MaterialTheme.typography.bodyLarge)
                }
            }
        }
        return
    }

    NavHost(navController, startDestination = Routes.HOME) {
        composable(Routes.HOME) {
            HomeScreen(
                books = ready.bookSummaries,
                scope = ready.scope,
                onOpenBook = { b -> navController.navigate(Routes.book(b)) },
                onAbout = { navController.navigate(Routes.ABOUT) }
            )
        }
        composable(Routes.ABOUT) {
            AboutScreen(
                version = ready.metaVersion,
                scope = ready.scope,
                totals = ready.catalog.totals,
                onBack = { navController.popBackStack() }
            )
        }
        composable(
            Routes.BOOK,
            arguments = listOf(navArgument("book") { type = NavType.StringType })
        ) { e ->
            val book = e.arguments?.getString("book") ?: return@composable
            var chapters by remember(book) { mutableStateOf<List<ChapterIndex>?>(null) }
            var err by remember(book) { mutableStateOf<String?>(null) }
            LaunchedEffect(book) {
                runCatching { ready.ensureBook(book) }
                    .onSuccess { chapters = it.chapters }
                    .onFailure { err = it.message }
            }
            when {
                err != null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(err ?: "Error", color = MaterialTheme.colorScheme.error)
                }
                chapters == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator()
                        Spacer(Modifier.height(12.dp))
                        Text("Loading ${BookTitles.title(book)}…")
                    }
                }
                else -> BookScreen(
                    book = book,
                    chapters = chapters!!,
                    onBack = { navController.popBackStack() },
                    onOpenChapter = { b, c -> navController.navigate(Routes.chapter(b, c)) }
                )
            }
        }
        composable(
            Routes.CHAPTER,
            arguments = listOf(
                navArgument("book") { type = NavType.StringType },
                navArgument("chapter") { type = NavType.IntType }
            )
        ) { e ->
            val book = e.arguments?.getString("book") ?: "Gen"
            val chapter = e.arguments?.getInt("chapter") ?: 1
            var readyChapter by remember(book, chapter) { mutableStateOf(false) }
            var err by remember(book, chapter) { mutableStateOf<String?>(null) }
            LaunchedEffect(book, chapter) {
                runCatching { ready.ensureBook(book) }
                    .onSuccess { readyChapter = true }
                    .onFailure { err = it.message }
            }
            when {
                err != null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(err ?: "Error", color = MaterialTheme.colorScheme.error)
                }
                !readyChapter -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                else -> ChapterScreen(
                    book = book,
                    chapter = chapter,
                    verses = ready.versesInChapter(book, chapter),
                    onBack = { navController.popBackStack() },
                    onOpenVerse = { id -> navController.navigate(Routes.verse(id)) }
                )
            }
        }
        composable(
            Routes.VERSE,
            arguments = listOf(navArgument("verseId") { type = NavType.StringType })
        ) { e ->
            val id = e.arguments?.getString("verseId") ?: return@composable
            val book = id.substringBefore('.')
            var verseReady by remember(id) { mutableStateOf(ready.verse(id) != null && ready.glossesReady) }
            var err by remember(id) { mutableStateOf<String?>(null) }
            LaunchedEffect(id) {
                runCatching {
                    ready.ensureBook(book)
                    ready.ensureGlosses()
                }
                    .onSuccess { verseReady = true }
                    .onFailure { err = it.message }
            }
            when {
                err != null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(err ?: "Error", color = MaterialTheme.colorScheme.error)
                }
                !verseReady || ready.verse(id) == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                else -> VerseScreen(
                    verse = ready.verse(id)!!,
                    resolveGloss = { ready.gloss(it) },
                    onBack = { navController.popBackStack() }
                )
            }
        }
    }
}
