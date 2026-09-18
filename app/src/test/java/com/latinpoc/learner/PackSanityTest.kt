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
    fun gen13_luxIsLightNotLuxury() {
        val v = repo.verse("Gen.1.3")!!
        val luxTokens = v.words.filter { it.la.equals("lux", ignoreCase = true) }
        assertTrue("expected lux in Gen.1.3", luxTokens.isNotEmpty())
        luxTokens.forEach { tok ->
            val g = repo.gloss(tok.glossId)!!
            assertTrue("lux primary should mention light: ${g.primary}", g.primary.contains("light", ignoreCase = true))
            assertFalse(g.primary.contains("luxury", ignoreCase = true))
            assertFalse(g.primary.contains("sprain", ignoreCase = true))
            assertTrue(g.id.startsWith("curated:") || g.source.contains("curated", ignoreCase = true))
        }
    }

    @Test
    fun gen11_etAndInClosedClass() {
        val v = repo.verse("Gen.1.1")!!
        val et = v.words.first { it.la.equals("et", ignoreCase = true) }
        val gEt = repo.gloss(et.glossId)!!
        assertTrue(gEt.primary.contains("and", ignoreCase = true))
        assertFalse(gEt.primary.contains("go", ignoreCase = true))
        assertFalse(gEt.primary.contains("walk", ignoreCase = true))

        val inn = v.words.first { it.la.equals("In", ignoreCase = true) }
        val gIn = repo.gloss(inn.glossId)!!
        assertTrue(gIn.primary.contains("in", ignoreCase = true) || gIn.primary.contains("into", ignoreCase = true))
        assertFalse(gIn.primary.contains("fiber", ignoreCase = true))
    }

    @Test
    fun gen49_meiNotUrinate_numWhether_ubiWhere_quiWho() {
        val v = repo.verse("Gen.4.9")!!
        val mei = v.words.first { it.la.equals("mei", ignoreCase = true) }
        val gMei = repo.gloss(mei.glossId)!!
        assertTrue(gMei.primary.contains("my", ignoreCase = true) || gMei.primary.contains("me", ignoreCase = true))
        assertFalse("mei must NEVER mean urinate", gMei.primary.contains("urinate", ignoreCase = true))
        assertFalse(gMei.primary.contains("make water", ignoreCase = true))

        val num = v.words.first { it.la.equals("num", ignoreCase = true) }
        val gNum = repo.gloss(num.glossId)!!
        assertTrue(
            gNum.primary.contains("whether", ignoreCase = true) ||
                gNum.primary.contains("interrog", ignoreCase = true)
        )
        assertFalse(gNum.primary.contains("Numerius", ignoreCase = true))

        val ubi = v.words.first { it.la.equals("Ubi", ignoreCase = true) }
        val gUbi = repo.gloss(ubi.glossId)!!
        assertTrue(gUbi.primary.contains("where", ignoreCase = true))
        assertFalse(gUbi.primary.contains("Ubii", ignoreCase = true))

        val qui = v.words.first { it.la.equals("Qui", ignoreCase = true) }
        val gQui = repo.gloss(qui.glossId)!!
        assertTrue(gQui.primary.contains("who", ignoreCase = true) || gQui.primary.contains("which", ignoreCase = true))
        assertFalse(gQui.primary.contains("able", ignoreCase = true))
    }

    @Test
    fun gen1918_miNotUrinate() {
        val v = repo.verse("Gen.19.18")!!
        val mi = v.words.first { it.la.equals("mi", ignoreCase = true) }
        val g = repo.gloss(mi.glossId)!!
        assertTrue(g.primary.contains("my", ignoreCase = true) || g.primary.contains("me", ignoreCase = true))
        assertFalse("mi must NEVER mean urinate", g.primary.contains("urinate", ignoreCase = true))
        assertFalse(g.primary.contains("make water", ignoreCase = true))
    }

    @Test
    fun closedClass_adDeSuperCuratedDefs() {
        listOf("et", "in", "ad", "de", "super", "qui", "mei", "mi", "ubi", "num", "lux", "meis", "meus", "quis").forEach { key ->
            val g = repo.gloss("curated:$key")
            assertNotNull("missing curated:$key in sample pack", g)
            assertFalse(g!!.primary.contains("urinate", ignoreCase = true))
            assertFalse(g.primary.contains("go, walk", ignoreCase = true))
            assertFalse(g.primary.contains("fiber", ignoreCase = true))
            assertFalse(g.primary.contains("Adam", ignoreCase = true))
            assertFalse(g.primary.contains("gods (pl.) on high", ignoreCase = true))
            assertFalse(g.primary.contains("luxury", ignoreCase = true))
        }
    }

    @Test
    fun gen223_meisMyMineNotUrinate() {
        val v = repo.verse("Gen.2.23")!!
        val meis = v.words.first { it.la.equals("meis", ignoreCase = true) }
        val g = repo.gloss(meis.glossId)!!
        assertTrue(
            "meis should be my/mine: ${g.primary}",
            g.primary.contains("my", ignoreCase = true) || g.primary.contains("mine", ignoreCase = true),
        )
        assertFalse("meis must NEVER mean urinate", g.primary.contains("urinate", ignoreCase = true))
        assertFalse(g.primary.contains("make water", ignoreCase = true))
        assertTrue(
            "expected curated meus-family gloss, got ${g.id}",
            g.id.startsWith("curated:") || g.source.contains("curated", ignoreCase = true),
        )
        assertFalse("must not bind w:mei", meis.glossId == "w:mei")
    }

    @Test
    fun gen311_quisWhoNotHow() {
        val v = repo.verse("Gen.3.11")!!
        val quis = v.words.first { it.la.equals("Quis", ignoreCase = true) }
        val g = repo.gloss(quis.glossId)!!
        assertTrue("quis should be who?: ${g.primary}", g.primary.contains("who", ignoreCase = true))
        assertFalse("quis must NOT mean how?", g.primary.contains("how?", ignoreCase = true))
        assertFalse("quis must NOT be how-so ADV", g.primary.lowercase().startsWith("how"))
        assertTrue(
            "expected curated quis, got ${g.id}",
            g.id == "curated:quis" || g.id.startsWith("curated:"),
        )
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
