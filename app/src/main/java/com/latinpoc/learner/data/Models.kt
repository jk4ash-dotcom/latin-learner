package com.latinpoc.learner.data

import kotlinx.serialization.Serializable

@Serializable
data class Catalog(
    val name: String,
    val version: String,
    val generatedAt: String = "",
    val scope: String = "",
    val navOrder: String = "",
    val latinPin: String = "",
    val books: List<CatalogBook> = emptyList(),
    val glossesAsset: String = "data/glosses.json",
    val glossesAssetGz: String? = "data/glosses.json.gz",
    val totals: CatalogTotals = CatalogTotals()
)

@Serializable
data class CatalogBook(
    val osis: String,
    val title: String,
    val division: String = "",
    val order: Int = 0,
    val chapters: Int = 0,
    val verses: Int = 0,
    val asset: String = "",
    val assetGz: String? = null
)

@Serializable
data class CatalogTotals(
    val books: Int = 0,
    val verses: Int = 0,
    val glosses: Int = 0,
    val glossHits: Int = 0,
    val glossStubs: Int = 0,
    val phoneticPending: Int = 0
)

@Serializable
data class Pack(
    val meta: PackMeta,
    val chapters: List<ChapterIndex>,
    val verses: List<Verse>,
    val glosses: Map<String, Gloss> = emptyMap()
)

@Serializable
data class PackMeta(
    val name: String,
    val version: String,
    val generatedAt: String = "",
    val scope: String = "",
    val book: String = "",
    val title: String = "",
    val division: String = "",
    val latin: Map<String, String> = emptyMap(),
    val english: Map<String, String> = emptyMap(),
    val phonetics: Map<String, String> = emptyMap(),
    val glosses: Map<String, String> = emptyMap(),
    val gaps: List<String> = emptyList()
)

@Serializable
data class ChapterIndex(
    val book: String,
    val chapter: Int,
    val verseIds: List<String>
)

@Serializable
data class Verse(
    val id: String,
    val book: String,
    val chapter: Int,
    val verse: Int,
    val latin: String = "",
    val english: EnglishLine,
    val words: List<Token>
)

@Serializable
data class EnglishLine(
    val text: String,
    val source: String = "Douay-Rheims Challoner",
    val license: String = "Public Domain"
)

@Serializable
data class Token(
    val la: String,
    val lemmaId: String? = null,
    val phonetic: String,
    val phoneticScheme: String = "ecclesiastical-italianate-v1",
    val phoneticPending: Boolean = false,
    val glossId: String? = null
)

@Serializable
data class Gloss(
    val id: String,
    val primary: String,
    val senses: List<String> = emptyList(),
    val source: String = "",
    val definition: String? = null,
    val note: String? = null
)
