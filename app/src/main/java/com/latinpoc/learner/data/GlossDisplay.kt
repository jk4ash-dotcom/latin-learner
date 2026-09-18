package com.latinpoc.learner.data

/**
 * UI-facing gloss presentation. Stubs stay clearly labeled for Scriba.
 */
object GlossDisplay {
    data class Shown(
        val primary: String,
        val senses: List<String>,
        val definition: String?,
        val source: String,
        val policyNote: String?
    )

    fun displayTokens(verse: Verse): List<Token> = verse.words

    fun forToken(token: Token, gloss: Gloss?): Shown {
        if (gloss == null) {
            return Shown(
                primary = "[no gloss]",
                senses = emptyList(),
                definition = null,
                source = "",
                policyNote = "Gloss unresolved — Scriba may fill."
            )
        }
        val stub = gloss.id.startsWith("stub:") || gloss.source == "stub"
        return Shown(
            primary = gloss.primary,
            senses = gloss.senses,
            definition = gloss.definition,
            source = gloss.source,
            policyNote = when {
                stub -> "Stub — pending Scriba (Whitaker miss)."
                token.phoneticPending -> "Phonetic marked pending for Scriba review."
                else -> gloss.note
            }
        )
    }
}
