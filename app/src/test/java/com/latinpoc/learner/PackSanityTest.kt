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
        listOf(
            "et", "in", "ad", "de", "super", "qui", "mei", "mi", "ubi", "num", "lux", "meis", "meus", "quis",
            "illud", "ille", "manum", "manus", "adam", "adae", "terra", "terram", "terrae", "terras", "terris",
            "caeli", "caelum", "dies", "die", "diem", "lucem", "aqua", "aquae", "aquas",
            "tenebrae", "faciem", "facie", "facies", "anima", "animam", "imaginem", "species", "speciem", "stellas",
        ).forEach { key ->
            val g = repo.gloss("curated:$key")
            assertNotNull("missing curated:$key in sample pack", g)
            assertFalse(g!!.primary.contains("urinate", ignoreCase = true))
            assertFalse(g.primary.contains("go, walk", ignoreCase = true))
            assertFalse(g.primary.contains("fiber", ignoreCase = true))
            // curated:ad must not be Adam; curated:adam / curated:adae ARE Adam
            if (key != "adam" && key != "adae") {
                assertFalse(g.primary.contains("Adam", ignoreCase = true))
            }
            assertFalse(g.primary.contains("plow", ignoreCase = true))
            assertFalse(g.primary.contains("gods (pl.) on high", ignoreCase = true))
            assertFalse(g.primary.contains("luxury", ignoreCase = true))
            assertFalse(g.primary.contains("lust", ignoreCase = true))
            assertFalse(g.primary.contains("fall in love", ignoreCase = true))
            assertFalse(g.primary.contains("frighten", ignoreCase = true))
            assertFalse(g.primary.contains("terrify", ignoreCase = true))
            assertFalse(g.primary.contains("scare", ignoreCase = true))
            assertFalse(g.primary.contains("beer", ignoreCase = true))
            assertFalse(g.primary.contains("quarter tone", ignoreCase = true))
            assertFalse(g.primary.contains("diesis", ignoreCase = true))
            assertFalse(g.primary.contains("grove", ignoreCase = true))
            assertFalse(g.primary.contains("fetch", ignoreCase = true))
            assertFalse(g.primary.contains("darken", ignoreCase = true))
            assertFalse(g.primary.contains("imagine", ignoreCase = true))
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
    fun gen33_illudThatItNotMockSexual() {
        val v = repo.verse("Gen.3.3")!!
        val illud = v.words.first { it.la.equals("illud", ignoreCase = true) }
        val g = repo.gloss(illud.glossId)!!
        assertTrue(
            "illud should be that/it: ${g.primary}",
            g.primary.contains("that", ignoreCase = true) || g.primary.contains("it", ignoreCase = true),
        )
        assertFalse("illud must NEVER mean mock/ridicule", g.primary.contains("mock", ignoreCase = true))
        assertFalse("illud must NEVER mean ridicule", g.primary.contains("ridicule", ignoreCase = true))
        assertFalse("illud must NEVER mean sexual", g.primary.contains("sexual", ignoreCase = true))
        assertTrue(
            "expected curated illud, got ${g.id}",
            g.id == "curated:illud" || g.id.startsWith("curated:"),
        )
        assertFalse("must not bind w:illud (illūdō)", illud.glossId == "w:illud")
    }

    @Test
    fun gen322_manumHandNotManeoSexualOvernight() {
        val v = repo.verse("Gen.3.22")!!
        val manum = v.words.first { it.la.equals("manum", ignoreCase = true) }
        val g = repo.gloss(manum.glossId)!!
        assertTrue("manum should be hand: ${g.primary}", g.primary.contains("hand", ignoreCase = true))
        assertFalse("manum must NEVER mean remain/abide", g.primary.contains("remain", ignoreCase = true))
        assertFalse("manum must NEVER mean abide", g.primary.contains("abide", ignoreCase = true))
        assertFalse("manum must NEVER mean spend the night", g.primary.contains("night", ignoreCase = true))
        assertFalse("manum must NEVER mean sexual", g.primary.contains("sexual", ignoreCase = true))
        assertTrue(
            "expected curated manum/manus, got ${g.id}",
            g.id.startsWith("curated:") || g.source.contains("curated", ignoreCase = true),
        )
        assertFalse("must not bind w:man (maneō)", manum.glossId == "w:man")
    }

    @Test
    fun gen23_adamProperNameNeverLust() {
        val verses = listOf(
            "Gen.2.19", "Gen.2.20", "Gen.2.21", "Gen.2.22", "Gen.2.23", "Gen.2.25",
            "Gen.3.8", "Gen.3.9", "Gen.3.12", "Gen.3.20", "Gen.3.22", "Gen.3.24",
        )
        var adamCount = 0
        for (id in verses) {
            val v = repo.verse(id)!!
            for (w in v.words.filter { it.la.equals("Adam", ignoreCase = true) }) {
                adamCount++
                val g = repo.gloss(w.glossId)!!
                assertTrue(
                    "Adam should be proper name: ${g.primary} @ $id",
                    g.primary.contains("Adam", ignoreCase = true),
                )
                assertFalse("Adam must NEVER mean lust @ $id", g.primary.contains("lust", ignoreCase = true))
                assertFalse(
                    "Adam must NEVER mean fall in love @ $id",
                    g.primary.contains("fall in love", ignoreCase = true),
                )
                assertFalse(
                    "Adam must NEVER mean love passionately @ $id",
                    g.primary.contains("love passionately", ignoreCase = true),
                )
                assertTrue(
                    "expected curated adam, got ${g.id} @ $id",
                    g.id == "curated:adam" || g.id.startsWith("curated:"),
                )
                assertFalse("must not bind w:adam (adamō) @ $id", w.glossId == "w:adam")
            }
        }
        assertTrue("expected Gen.2–3 Adam tokens, got $adamCount", adamCount >= 14)
    }

    @Test
    fun gen220_317_321_adaeAdamGenitiveNeverPlow() {
        val verses = listOf("Gen.2.20", "Gen.3.17", "Gen.3.21")
        var adaeCount = 0
        for (id in verses) {
            val v = repo.verse(id)!!
            val tokens = v.words.filter {
                it.la.equals("Adæ", ignoreCase = true) ||
                    it.la.equals("Adae", ignoreCase = true) ||
                    it.lemmaId == "adae"
            }
            assertTrue("expected Adæ/Adae in $id", tokens.isNotEmpty())
            for (w in tokens) {
                adaeCount++
                val g = repo.gloss(w.glossId)!!
                assertTrue(
                    "Adæ should be Adam (gen.): ${g.primary} @ $id",
                    g.primary.contains("Adam", ignoreCase = true),
                )
                assertFalse("Adæ must NEVER mean plow @ $id", g.primary.contains("plow", ignoreCase = true))
                assertFalse("Adæ must NEVER mean plough @ $id", g.primary.contains("plough", ignoreCase = true))
                assertTrue(
                    "expected curated adae, got ${g.id} @ $id",
                    g.id == "curated:adae" || g.id.startsWith("curated:"),
                )
                assertFalse("must not bind w:adar (plow) @ $id", w.glossId == "w:adar")
            }
        }
        assertTrue("expected >=3 Adæ tokens in Gen.2.20/3.17/3.21, got $adaeCount", adaeCount >= 3)
    }

    @Test
    fun gen11_terramEarthLandNotTerror() {
        val v = repo.verse("Gen.1.1")!!
        val terram = v.words.first { it.la.equals("terram", ignoreCase = true) }
        val g = repo.gloss(terram.glossId)!!
        assertTrue(
            "terram should be earth/land: ${g.primary}",
            g.primary.contains("earth", ignoreCase = true) || g.primary.contains("land", ignoreCase = true),
        )
        assertFalse("terram must NEVER mean frighten", g.primary.contains("frighten", ignoreCase = true))
        assertFalse("terram must NEVER mean terrify", g.primary.contains("terrify", ignoreCase = true))
        assertFalse("terram must NEVER mean scare", g.primary.contains("scare", ignoreCase = true))
        assertFalse("terram must NEVER mean terror", g.primary.contains("terror", ignoreCase = true))
        assertTrue(
            "expected curated terram, got ${g.id}",
            g.id == "curated:terram" || g.id.startsWith("curated:"),
        )
        assertFalse("must not bind w:terr (terreō)", terram.glossId == "w:terr")
    }

    @Test
    fun gen1to3_terraFamilyEarthLandNeverTerreo() {
        val nounSurfaces = setOf(
            "terra", "terram", "terrae", "terræ", "terras", "terris", "terrarum",
            "terraque", "terramque", "terraeque", "terrasque", "terrisque", "terrarumque",
        )
        var count = 0
        for (ch in 1..3) {
            // sample pack has all Gen.1–3 verses
            val verses = (1..50).mapNotNull { n -> repo.verse("Gen.$ch.$n") }
            for (v in verses) {
                for (w in v.words) {
                    val la = w.la.lowercase()
                    val lid = (w.lemmaId ?: "").lowercase()
                    val isNoun = la in nounSurfaces || lid in nounSurfaces ||
                        nounSurfaces.any { la.replace("æ", "ae") == it || lid.replace("æ", "ae") == it }
                    if (!isNoun) continue
                    // exclude terror / terrestris / terret-family if ever present
                    if (la.startsWith("terror") || lid.startsWith("terror")) continue
                    if (la.startsWith("terrestr") || lid.startsWith("terrestr")) continue
                    if (la.startsWith("terrib") || lid.startsWith("terrib")) continue
                    count++
                    val g = repo.gloss(w.glossId)!!
                    assertTrue(
                        "terra-noun should be earth/land: ${g.primary} @ ${v.id} ${w.la}",
                        g.primary.contains("earth", ignoreCase = true) ||
                            g.primary.contains("land", ignoreCase = true) ||
                            g.primary.contains("ground", ignoreCase = true),
                    )
                    assertFalse("must NEVER frighten @ ${v.id} ${w.la}", g.primary.contains("frighten", ignoreCase = true))
                    assertFalse("must NEVER terrify @ ${v.id} ${w.la}", g.primary.contains("terrify", ignoreCase = true))
                    assertFalse("must NEVER scare @ ${v.id} ${w.la}", g.primary.contains("scare", ignoreCase = true))
                    assertFalse("must NEVER terror @ ${v.id} ${w.la}", g.primary.contains("terror", ignoreCase = true))
                    assertFalse("must not bind w:terr @ ${v.id}", w.glossId == "w:terr")
                    assertTrue(
                        "expected curated terra-family, got ${g.id} @ ${v.id}",
                        g.id.startsWith("curated:") || g.source.contains("curated", ignoreCase = true),
                    )
                }
            }
        }
        assertTrue("expected Gen.1–3 terra-noun tokens, got $count", count >= 20)
    }

    @Test
    fun gen1020_3512_terraEncliticsEarthLand() {
        val cases = listOf(
            "Gen.10.20" to "terrisque",
            "Gen.35.12" to "terramque",
        )
        for ((id, surface) in cases) {
            val v = repo.verse(id)!!
            val tok = v.words.first {
                it.la.equals(surface, ignoreCase = true) ||
                    (it.lemmaId ?: "").equals(surface, ignoreCase = true)
            }
            val g = repo.gloss(tok.glossId)!!
            assertTrue(
                "$surface should be earth/land: ${g.primary} @ $id",
                g.primary.contains("earth", ignoreCase = true) || g.primary.contains("land", ignoreCase = true),
            )
            assertFalse("$surface must NEVER frighten @ $id", g.primary.contains("frighten", ignoreCase = true))
            assertFalse("must not bind w:terr @ $id", tok.glossId == "w:terr")
            assertTrue(
                "expected curated for $surface, got ${g.id}",
                g.id.startsWith("curated:"),
            )
        }
    }


    @Test
    fun gen114_caeliHeavenNotBeer() {
        val v = repo.verse("Gen.1.14")!!
        val caeli = v.words.first {
            it.la.equals("cæli", ignoreCase = true) ||
                it.la.equals("caeli", ignoreCase = true) ||
                (it.lemmaId ?: "") == "caeli"
        }
        val g = repo.gloss(caeli.glossId)!!
        assertTrue(
            "caeli should be heaven(s): ${g.primary}",
            g.primary.contains("heaven", ignoreCase = true) || g.primary.contains("sky", ignoreCase = true),
        )
        assertFalse("caeli must NEVER mean beer", g.primary.contains("beer", ignoreCase = true))
        assertTrue("expected curated caeli, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:caeli (beer)", caeli.glossId == "w:caeli")
    }

    @Test
    fun gen15_diesDayNotDiesis() {
        val v = repo.verse("Gen.1.5")!!
        val dies = v.words.first { it.la.equals("dies", ignoreCase = true) }
        val g = repo.gloss(dies.glossId)!!
        assertTrue("dies should be day: ${g.primary}", g.primary.contains("day", ignoreCase = true))
        assertFalse("dies must NEVER mean quarter tone", g.primary.contains("quarter", ignoreCase = true))
        assertFalse("dies must NEVER mean diesis", g.primary.contains("diesis", ignoreCase = true))
        assertFalse("dies must NEVER mean tone", g.primary.contains("tone", ignoreCase = true))
        assertTrue("expected curated dies, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:dies (diesis)", dies.glossId == "w:dies")
    }

    @Test
    fun gen1to3_diesFamilyDayNeverDiesis() {
        val surfaces = setOf(
            "dies", "die", "diem", "diei", "diebus", "dierum",
            "diesque", "dieque", "diemque", "dieique", "diebusque", "dierumque",
        )
        var count = 0
        for (ch in 1..3) {
            val verses = (1..50).mapNotNull { n -> repo.verse("Gen.$ch.$n") }
            for (v in verses) {
                for (w in v.words) {
                    val la = w.la.lowercase().replace("æ", "ae")
                    val lid = (w.lemmaId ?: "").lowercase()
                    if (la !in surfaces && lid !in surfaces) continue
                    count++
                    val g = repo.gloss(w.glossId)!!
                    assertTrue(
                        "dies-family should be day: ${g.primary} @ ${v.id} ${w.la}",
                        g.primary.contains("day", ignoreCase = true),
                    )
                    assertFalse("must NEVER diesis @ ${v.id}", g.primary.contains("diesis", ignoreCase = true))
                    assertFalse("must NEVER quarter @ ${v.id}", g.primary.contains("quarter", ignoreCase = true))
                    assertFalse("must not bind w:dies @ ${v.id}", w.glossId == "w:dies")
                    assertTrue("expected curated dies-family, got ${g.id}", g.id.startsWith("curated:"))
                }
            }
        }
        assertTrue("expected Gen.1–3 dies-family tokens, got $count", count >= 15)
    }

    @Test
    fun gen14_lucemLightNotGrove() {
        val v = repo.verse("Gen.1.4")!!
        val lucem = v.words.first { it.la.equals("lucem", ignoreCase = true) }
        val g = repo.gloss(lucem.glossId)!!
        assertTrue("lucem should be light: ${g.primary}", g.primary.contains("light", ignoreCase = true))
        assertFalse("lucem must NEVER mean grove", g.primary.contains("grove", ignoreCase = true))
        assertFalse("lucem must NEVER mean luxury", g.primary.contains("luxury", ignoreCase = true))
        assertTrue("expected curated lucem, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen12_aquasWaterNotFetch() {
        val v = repo.verse("Gen.1.2")!!
        val aquas = v.words.first { it.la.equals("aquas", ignoreCase = true) }
        val g = repo.gloss(aquas.glossId)!!
        assertTrue(
            "aquas should be water(s): ${g.primary}",
            g.primary.contains("water", ignoreCase = true),
        )
        assertFalse("aquas must NEVER mean fetch", g.primary.contains("fetch", ignoreCase = true))
        assertFalse("aquas must NEVER mean bring water", g.primary.contains("bring", ignoreCase = true))
        assertTrue("expected curated aqua-family, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind fetch-water w:aqu", aquas.glossId == "w:aqu" && g.primary.contains("fetch", ignoreCase = true))
    }

    @Test
    fun gen1to3_aquaFamilyWaterNeverFetch() {
        val surfaces = setOf(
            "aqua", "aquae", "aquam", "aquas", "aquarum", "aquis",
            "aquaque", "aquaeque", "aquamque", "aquasque", "aquarumque", "aquisque",
        )
        var count = 0
        for (ch in 1..3) {
            val verses = (1..50).mapNotNull { n -> repo.verse("Gen.$ch.$n") }
            for (v in verses) {
                for (w in v.words) {
                    val la = w.la.lowercase().replace("æ", "ae")
                    val lid = (w.lemmaId ?: "").lowercase()
                    if (la.startsWith("aquilon") || lid.startsWith("aquilon")) continue
                    if (la !in surfaces && lid !in surfaces) continue
                    count++
                    val g = repo.gloss(w.glossId)!!
                    assertTrue(
                        "aqua-noun should be water: ${g.primary} @ ${v.id} ${w.la}",
                        g.primary.contains("water", ignoreCase = true),
                    )
                    assertFalse("must NEVER fetch @ ${v.id}", g.primary.contains("fetch", ignoreCase = true))
                    assertTrue("expected curated aqua-family @ ${v.id}", g.id.startsWith("curated:"))
                }
            }
        }
        assertTrue("expected Gen.1–3 aqua-noun tokens, got $count", count >= 10)
    }

    @Test
    fun gen12_tenebraeDarknessNotDarken() {
        val v = repo.verse("Gen.1.2")!!
        val tok = v.words.first {
            it.la.equals("tenebrae", ignoreCase = true) ||
                it.la.equals("tenebræ", ignoreCase = true) ||
                (it.lemmaId ?: "") == "tenebrae"
        }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            "tenebrae should be darkness: ${g.primary}",
            g.primary.contains("darkness", ignoreCase = true) || g.primary.contains("dark", ignoreCase = true),
        )
        assertFalse("tenebrae must NEVER mean darken", g.primary.contains("darken", ignoreCase = true))
        assertFalse("tenebrae must NEVER mean hold", g.primary.contains("hold", ignoreCase = true))
        assertTrue("expected curated tenebrae, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen12_faciemFaceNotMake() {
        val v = repo.verse("Gen.1.2")!!
        val faciem = v.words.first { it.la.equals("faciem", ignoreCase = true) }
        val g = repo.gloss(faciem.glossId)!!
        assertTrue(
            "faciem should be face: ${g.primary}",
            g.primary.contains("face", ignoreCase = true) || g.primary.contains("countenance", ignoreCase = true),
        )
        assertFalse("faciem must NEVER mean make", g.primary.contains("make", ignoreCase = true))
        assertFalse("faciem must NEVER mean build", g.primary.contains("build", ignoreCase = true))
        assertTrue("expected curated faciem, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen121_animamSoulNotMind() {
        val v = repo.verse("Gen.1.21")!!
        val animam = v.words.first { it.la.equals("animam", ignoreCase = true) }
        val g = repo.gloss(animam.glossId)!!
        assertTrue(
            "animam should be soul/living being: ${g.primary}",
            g.primary.contains("soul", ignoreCase = true) ||
                g.primary.contains("living", ignoreCase = true) ||
                g.primary.contains("life", ignoreCase = true),
        )
        assertFalse(
            "animam must NOT be mind-only",
            g.primary.trim().equals("mind", ignoreCase = true),
        )
        assertTrue("expected curated anima-family, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen126_imaginemImageNotImagine() {
        val v = repo.verse("Gen.1.26")!!
        val imaginem = v.words.first { it.la.equals("imaginem", ignoreCase = true) }
        val g = repo.gloss(imaginem.glossId)!!
        assertTrue("imaginem should be image: ${g.primary}", g.primary.contains("image", ignoreCase = true))
        assertFalse("imaginem must NEVER mean imagine", g.primary.contains("imagine", ignoreCase = true))
        assertTrue("expected curated imaginem, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen112_speciemKindNotLook() {
        val v = repo.verse("Gen.1.12")!!
        val speciem = v.words.first { it.la.equals("speciem", ignoreCase = true) }
        val g = repo.gloss(speciem.glossId)!!
        assertTrue(
            "speciem should be kind/species: ${g.primary}",
            g.primary.contains("kind", ignoreCase = true) ||
                g.primary.contains("species", ignoreCase = true) ||
                g.primary.contains("appearance", ignoreCase = true),
        )
        assertFalse("speciem must NEVER mean look at", g.primary.contains("look", ignoreCase = true))
        assertTrue("expected curated speciem, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen116_stellasStarsNotSetWithStars() {
        val v = repo.verse("Gen.1.16")!!
        val stellas = v.words.first { it.la.equals("stellas", ignoreCase = true) }
        val g = repo.gloss(stellas.glossId)!!
        assertTrue("stellas should be stars: ${g.primary}", g.primary.contains("star", ignoreCase = true))
        assertFalse("stellas must NEVER mean set/furnish with stars", g.primary.contains("furnish", ignoreCase = true))
        assertFalse("stellas must NEVER mean set with stars", g.primary.lowercase().contains("set/") || g.primary.lowercase().startsWith("set "))
        assertTrue("expected curated stellas, got ${g.id}", g.id.startsWith("curated:"))
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
