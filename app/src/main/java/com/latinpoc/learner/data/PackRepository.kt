package com.latinpoc.learner.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import java.io.BufferedReader
import java.io.FileNotFoundException
import java.io.IOException
import java.io.InputStream
import java.io.InputStreamReader
import java.io.PushbackInputStream
import java.util.zip.GZIPInputStream

/**
 * Offline catalog + per-book lazy packs (gzip assets) + shared gloss catalog.
 * Loads off the main thread. aapt2 may strip `.gz` — [readAssetText] handles both.
 */
class PackRepository private constructor(
    val catalog: Catalog,
    @Volatile private var glosses: Map<String, Gloss>?,
    private val books: MutableMap<String, Pack>,
    private val bookIndex: MutableMap<String, BookIndex>,
    private val assetOpener: (String) -> InputStream,
    private val glossCandidates: List<String>
) {
    val metaVersion: String get() = catalog.version
    val scope: String get() = catalog.scope
    val bookSummaries: List<CatalogBook> get() = catalog.books

    val glossesReady: Boolean get() = glosses != null

    fun chaptersFor(book: String): List<ChapterIndex> =
        books[book]?.chapters ?: emptyList()

    fun verse(id: String): Verse? {
        val book = id.substringBefore('.')
        bookIndex[book]?.byId?.get(id)?.let { return it }
        return books[book]?.verses?.firstOrNull { it.id == id }
    }

    fun gloss(id: String?): Gloss? {
        val key = id ?: return null
        return glosses?.get(key)
    }

    fun versesInChapter(book: String, chapter: Int): List<Verse> {
        bookIndex[book]?.byChapter?.get(chapter)?.let { return it }
        return books[book]?.verses?.filter { it.book == book && it.chapter == chapter } ?: emptyList()
    }

    fun isBookLoaded(book: String): Boolean = books.containsKey(book)

    suspend fun ensureGlosses(): Map<String, Gloss> = withContext(Dispatchers.IO) {
        glosses?.let { return@withContext it }
        glossMutex.withLock {
            glosses?.let { return@withLock it }
            val text = readAssetText(assetOpener, *glossCandidates.toTypedArray())
            val loaded: Map<String, Gloss> = json.decodeFromString(text)
            glosses = loaded
            loaded
        }
    }

    suspend fun ensureBook(book: String): Pack = withContext(Dispatchers.IO) {
        books[book]?.let { return@withContext it }
        bookMutex.withLock {
            books[book]?.let { return@withLock it }
            val summary = catalog.books.find { it.osis == book }
                ?: error("Unknown book $book")
            val candidates = assetCandidates(summary.assetGz, summary.asset)
            val text = readAssetText(assetOpener, *candidates.toTypedArray())
            val pack = json.decodeFromString(Pack.serializer(), text)
            books[book] = pack
            bookIndex[book] = BookIndex.from(pack)
            pack
        }
    }

    private val bookMutex = Mutex()
    private val glossMutex = Mutex()

    private data class BookIndex(
        val byId: Map<String, Verse>,
        val byChapter: Map<Int, List<Verse>>
    ) {
        companion object {
            fun from(pack: Pack): BookIndex {
                val byId = HashMap<String, Verse>(pack.verses.size)
                val byChapter = HashMap<Int, MutableList<Verse>>()
                for (v in pack.verses) {
                    byId[v.id] = v
                    byChapter.getOrPut(v.chapter) { mutableListOf() }.add(v)
                }
                val ordered = HashMap<Int, List<Verse>>(byChapter.size)
                for (ch in pack.chapters) {
                    val list = ch.verseIds.mapNotNull { byId[it] }
                    if (list.isNotEmpty()) ordered[ch.chapter] = list
                }
                for ((ch, list) in byChapter) {
                    ordered.putIfAbsent(ch, list)
                }
                return BookIndex(byId, ordered)
            }
        }
    }

    companion object {
        private const val CATALOG = "data/catalog.json"
        private const val GLOSSES_GZ = "data/glosses.json.gz"
        private const val GLOSSES_PLAIN = "data/glosses.json"

        @Volatile
        private var instance: PackRepository? = null

        private val json = Json {
            ignoreUnknownKeys = true
            isLenient = true
        }

        fun normalizeAssetPath(path: String): String {
            val trimmed = path.trim().removePrefix("/")
            return if (trimmed.startsWith("data/")) trimmed else "data/$trimmed"
        }

        fun assetCandidates(vararg paths: String?): List<String> =
            paths.filterNotNull()
                .map { it.trim() }
                .filter { it.isNotEmpty() }
                .map { normalizeAssetPath(it) }
                .distinct()

        fun readAssetText(opener: (String) -> InputStream, vararg candidates: String): String {
            require(candidates.isNotEmpty()) { "No asset candidates" }
            var last: Exception? = null
            for (path in candidates) {
                try {
                    opener(path).use { raw ->
                        return decodePossiblyGzipped(raw)
                    }
                } catch (e: FileNotFoundException) {
                    last = e
                } catch (e: IOException) {
                    last = e
                }
            }
            throw IOException(
                "Missing asset (tried: ${candidates.joinToString()})",
                last
            )
        }

        fun decodePossiblyGzipped(raw: InputStream): String {
            val pushback = PushbackInputStream(raw, 2)
            val header = ByteArray(2)
            val n = pushback.read(header)
            if (n > 0) {
                pushback.unread(header, 0, n)
            }
            val stream: InputStream =
                if (n == 2 && header[0] == 0x1f.toByte() && header[1] == 0x8b.toByte()) {
                    GZIPInputStream(pushback)
                } else {
                    pushback
                }
            return BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { it.readText() }
        }

        fun parseCombined(text: String): PackRepository {
            val pack = json.decodeFromString(Pack.serializer(), text)
            val catalog = Catalog(
                name = pack.meta.name,
                version = pack.meta.version,
                scope = pack.meta.scope,
                books = pack.chapters
                    .map { it.book }
                    .distinct()
                    .map { osis ->
                        val chs = pack.chapters.filter { it.book == osis }
                        CatalogBook(
                            osis = osis,
                            title = BookTitles.title(osis),
                            chapters = chs.size,
                            verses = pack.verses.count { it.book == osis }
                        )
                    },
                totals = CatalogTotals(
                    books = pack.chapters.map { it.book }.distinct().size,
                    verses = pack.verses.size,
                    glosses = pack.glosses.size
                )
            )
            val byBook = pack.verses.groupBy { it.book }.mapValues { (book, verses) ->
                Pack(
                    meta = pack.meta.copy(book = book, title = BookTitles.title(book)),
                    chapters = pack.chapters.filter { it.book == book },
                    verses = verses,
                    glosses = emptyMap()
                )
            }.toMutableMap()
            val indexes = byBook.mapValues { (_, p) -> BookIndex.from(p) }.toMutableMap()
            return PackRepository(
                catalog,
                pack.glosses,
                byBook,
                indexes,
                { error("no assets in parseCombined") },
                emptyList()
            )
        }

        fun parse(text: String): PackRepository = parseCombined(text)

        suspend fun load(context: Context): PackRepository {
            instance?.let { return it }
            return withContext(Dispatchers.IO) {
                instance ?: synchronized(this@Companion) {
                    instance ?: run {
                        val appCtx = context.applicationContext
                        val opener: (String) -> InputStream = { path ->
                            appCtx.assets.open(path)
                        }
                        val catalogText = readAssetText(opener, CATALOG)
                        val catalog = json.decodeFromString(Catalog.serializer(), catalogText)
                        val glossCandidates = assetCandidates(
                            catalog.glossesAssetGz,
                            catalog.glossesAsset,
                            GLOSSES_GZ,
                            GLOSSES_PLAIN
                        )
                        PackRepository(
                            catalog,
                            glosses = null,
                            books = mutableMapOf(),
                            bookIndex = mutableMapOf(),
                            assetOpener = opener,
                            glossCandidates = glossCandidates
                        ).also { instance = it }
                    }
                }
            }
        }

        fun clearInstanceForTests() {
            instance = null
        }
    }
}
