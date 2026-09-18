package com.latinpoc.learner.navigation

object Routes {
    const val HOME = "home"
    const val ABOUT = "about"
    const val BOOK = "book/{book}"
    const val CHAPTER = "chapter/{book}/{chapter}"
    const val VERSE = "verse/{verseId}"
    fun book(book: String) = "book/$book"
    fun chapter(book: String, chapter: Int) = "chapter/$book/$chapter"
    fun verse(verseId: String) = "verse/$verseId"
}
