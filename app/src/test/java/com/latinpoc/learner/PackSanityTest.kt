package com.latinpoc.learner

import com.latinpoc.learner.data.GlossDisplay
import com.latinpoc.learner.data.PackRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.BeforeClass
import org.junit.Test

class PackSanityTest {
    companion object {
        private lateinit var repo: PackRepository

        @JvmStatic
        @BeforeClass
        fun loadPack() {
            val stream = PackSanityTest::class.java.classLoader!!
                .getResourceAsStream("data/pack_genesis_samples.json")
                ?: error("Missing test resource data/pack_genesis_samples.json")
            val text = stream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            repo = PackRepository.parseCombined(text)
        }
    }

    @Test
    fun gen11_latinTokensAndPhonetics() {
        val v = repo.verse("Gen.1.1")!!
        assertTrue(v.words.size >= 6)
        assertEquals("In", v.words[0].la)
        assertEquals("principio", v.words[1].la)
        assertEquals("creavit", v.words[2].la)
        assertEquals("Deus", v.words[3].la)
        v.words.forEach { t ->
            assertTrue(t.la.isNotBlank())
            assertTrue(t.phonetic.isNotBlank())
            assertEquals("ecclesiastical-italianate-v1", t.phoneticScheme)
        }
    }

    @Test
    fun gen11_englishIsDouayNotKjv() {
        val v = repo.verse("Gen.1.1")!!
        assertTrue(v.english.text.contains("beginning", ignoreCase = true))
        assertTrue(v.english.source.contains("Douay", ignoreCase = true))
        assertFalse(v.english.text.equals("In the beginning God created the heaven and the earth.", ignoreCase = true))
    }

    @Test
    fun gen11_deusIsGodNotMisuse() {
        val v = repo.verse("Gen.1.1")!!
        val deus = v.words.first { it.la == "Deus" }
        val g = repo.gloss(deus.glossId)!!
        assertTrue(g.primary.contains("God", ignoreCase = true))
        assertFalse(g.primary.contains("misuse", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:") || g.source.contains("curated", ignoreCase = true))
    }

    @Test
    fun gen27_dominusLordNotMistress_ejusNotAbjure() {
        val v = repo.verse("Gen.2.7")!!
        val dominus = v.words.first { it.la == "Dominus" }
        val gDom = repo.gloss(dominus.glossId)!!
        assertTrue(gDom.primary.contains("Lord", ignoreCase = true) || gDom.primary.contains("master", ignoreCase = true))
        assertFalse(gDom.primary.contains("mistress", ignoreCase = true))

        val ejus = v.words.first { it.la.equals("ejus", ignoreCase = true) }
        val gEj = repo.gloss(ejus.glossId)!!
        assertTrue(
            gEj.primary.contains("his", ignoreCase = true) ||
                gEj.primary.contains("her", ignoreCase = true)
        )
        assertFalse(gEj.primary.contains("abjure", ignoreCase = true))
    }

    @Test
    fun gen49_sumToBeNotHighest() {
        val v = repo.verse("Gen.4.9")!!
        val sum = v.words.first { it.la.equals("sum", ignoreCase = true) }
        val g = repo.gloss(sum.glossId)!!
        assertTrue(g.primary.contains("be", ignoreCase = true) || g.primary.contains("am", ignoreCase = true))
        assertFalse(g.primary.contains("highest", ignoreCase = true))
        assertFalse(g.primary.contains("take up", ignoreCase = true))
    }

    @Test
    fun sampleChapters_present() {
        listOf("Gen.1.1", "Gen.2.1", "Gen.3.1", "Gen.4.9").forEach { id ->
            val v = repo.verse(id)
            assertNotNull("missing $id", v)
            assertTrue(v!!.words.isNotEmpty())
            assertTrue(v.english.text.isNotBlank())
            assertEquals("Gen", v.book)
        }
    }

    @Test
    fun gloss_resolve_or_stub() {
        val v = repo.verse("Gen.1.1")!!
        v.words.forEach { w ->
            val g = repo.gloss(w.glossId)
            assertNotNull("expected gloss for ${w.la} id=${w.glossId}", g)
            assertTrue(g!!.primary.isNotBlank())
        }
    }

    @Test
    fun displayTokens_preservesOrder() {
        val v = repo.verse("Gen.1.1")!!
        val shown = GlossDisplay.displayTokens(v)
        assertEquals(v.words.map { it.la }, shown.map { it.la })
    }

    @Test
    fun catalog_hasGenesis() {
        assertTrue(repo.bookSummaries.any { it.osis == "Gen" })
    }
}
