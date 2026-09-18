package com.latinpoc.learner.data

object BookTitles {
    private val titles = mapOf(
        "Gen" to "Genesis"
    )

    fun title(osis: String): String = titles[osis] ?: osis

    fun chapterLabel(book: String, chapter: Int): String = "${title(book)} $chapter"

    fun verseLabel(book: String, chapter: Int, verse: Int): String =
        "${title(book)} $chapter:$verse"
}
