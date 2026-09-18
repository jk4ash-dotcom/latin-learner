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
            "tibi", "ei", "eos", "eis", "ea", "eas", "suas", "suum", "eam", "hoc", "vobis",
            "sit", "erunt", "essem", "esses", "esset", "sint",
            "sim", "sis", "simus", "sitis", "essent",
            "ero", "eris", "erit", "erimus", "eritis",
            "fuerit", "fuerint", "fuisset",
            "sara", "saram", "sarae", "sarai", "lot", "edom", "sex",
            "venit", "venite", "adamam", "adamae",
            "bala", "balam", "balae", "her", "sale", "salem",
            "suo", "suam", "suae", "suis", "tuus", "tuum", "tui", "tuae",
            "quem", "quid", "haec", "cui", "nos", "nobis", "se", "sibi", "vos", "his", "eorum",
            "dicens", "respondit", "tulit", "unus", "duo",
            "joseph", "abraham", "isaac", "esau", "noe",
            "ada", "sella", "sellae",
        ).forEach { key ->
            val g = repo.gloss("curated:$key")
            assertNotNull("missing curated:$key in sample pack", g)
            assertFalse(g!!.primary.contains("urinate", ignoreCase = true))
            assertFalse(g.primary.contains("go, walk", ignoreCase = true))
            assertFalse(g.primary.contains("fiber", ignoreCase = true))
            // curated:ad must not be Adam; curated:adam / curated:adae ARE Adam;
            // curated:adamam / curated:adamae are Admah (substring "Adam" OK)
            if (key != "adam" && key != "adae" && key != "adamam" && key != "adamae") {
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
            assertFalse(g.primary.contains("flute", ignoreCase = true))
            assertFalse(g.primary.contains("pipe", ignoreCase = true))
            assertFalse(g.primary.contains("Woe", ignoreCase = true))
            assertFalse(g.primary.contains("dawn", ignoreCase = true))
            assertFalse(g.primary.contains("urge", ignoreCase = true))
            assertFalse(g.primary.contains("recommend", ignoreCase = true))
            assertFalse(g.primary.contains("advice", ignoreCase = true))
            assertFalse(g.primary.contains("hockey", ignoreCase = true))
            assertFalse(g.primary.contains("allow", ignoreCase = true))
            assertFalse(g.primary.contains("permit", ignoreCase = true))
            assertFalse(g.primary.contains("pluck", ignoreCase = true))
            assertFalse(g.primary.contains("dig", ignoreCase = true))
            assertFalse(g.primary.contains("eat", ignoreCase = true))
            assertFalse(g.primary.contains("but if", ignoreCase = true))
            assertFalse(g.primary.contains("flatnosed", ignoreCase = true))
            assertFalse(g.primary.contains("thirst", ignoreCase = true))
            assertFalse(g.primary.contains("hedgehog", ignoreCase = true))
            assertFalse(g.primary.contains("hoe", ignoreCase = true))
            assertFalse(g.primary.contains("wash", ignoreCase = true))
            assertFalse(g.primary.contains("bathe", ignoreCase = true))
            assertFalse(g.primary.contains("subdue", ignoreCase = true))
            assertFalse(g.primary.contains("subjugate", ignoreCase = true))
            // numeral six may appear; bare sexual "sex" as whole primary blocked via dedicated tests
            assertFalse(g.primary.contains("go for sale", ignoreCase = true))
            assertFalse(g.primary.contains("bleat", ignoreCase = true))
            assertFalse(g.primary.contains("baa", ignoreCase = true))
            assertFalse(g.primary.contains("adhere", ignoreCase = true))
            assertFalse(g.primary.contains("leap", ignoreCase = true))
            assertFalse(g.primary.contains("jump", ignoreCase = true))
            assertFalse(g.primary.contains("basket", ignoreCase = true))
            assertFalse(g.primary.contains("make real", ignoreCase = true))
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
    fun gen311_tibiToForYouNotFlute() {
        val v = repo.verse("Gen.3.11")!!
        val tokens = v.words.filter { it.la.equals("tibi", ignoreCase = true) }
        assertTrue("expected tibi in Gen.3.11", tokens.isNotEmpty())
        tokens.forEach { tok ->
            val g = repo.gloss(tok.glossId)!!
            assertTrue(
                "tibi should be to/for you: ${g.primary}",
                g.primary.contains("you", ignoreCase = true) ||
                    g.primary.contains("to/", ignoreCase = true),
            )
            assertFalse("tibi must NEVER mean flute", g.primary.contains("flute", ignoreCase = true))
            assertFalse("tibi must NEVER mean pipe", g.primary.contains("pipe", ignoreCase = true))
            assertTrue("expected curated tibi, got ${g.id}", g.id.startsWith("curated:"))
            assertFalse("must not bind w:tibi (flute)", tok.glossId == "w:tibi")
        }
    }

    @Test
    fun gen216_eiToForHimHerNotAhWoe() {
        val v = repo.verse("Gen.2.16")!!
        val ei = v.words.first { it.la.equals("ei", ignoreCase = true) }
        val g = repo.gloss(ei.glossId)!!
        assertTrue(
            "ei should be to/for him/her: ${g.primary}",
            g.primary.contains("him", ignoreCase = true) ||
                g.primary.contains("her", ignoreCase = true) ||
                g.primary.contains("to/", ignoreCase = true),
        )
        assertFalse("ei must NEVER mean Ah", g.primary.contains("Ah", ignoreCase = true))
        assertFalse("ei must NEVER mean Woe", g.primary.contains("Woe", ignoreCase = true))
        assertFalse("ei must NEVER mean alas", g.primary.contains("alas", ignoreCase = true))
        assertTrue("expected curated ei, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:ei (Ah/Woe)", ei.glossId == "w:ei")
    }

    @Test
    fun gen127_eosThemNotDawn() {
        val v = repo.verse("Gen.1.27")!!
        val eos = v.words.first { it.la.equals("eos", ignoreCase = true) }
        val g = repo.gloss(eos.glossId)!!
        assertTrue(
            "eos should be them: ${g.primary}",
            g.primary.contains("them", ignoreCase = true) || g.primary.contains("those", ignoreCase = true),
        )
        assertFalse("eos must NEVER mean dawn", g.primary.contains("dawn", ignoreCase = true))
        assertTrue("expected curated eos, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:eos (dawn)", eos.glossId == "w:eos")
    }

    @Test
    fun gen122_eisToForThem() {
        val v = repo.verse("Gen.1.22")!!
        val eis = v.words.first { it.la.equals("eis", ignoreCase = true) }
        val g = repo.gloss(eis.glossId)!!
        assertTrue(
            "eis should be to/for them: ${g.primary}",
            g.primary.contains("them", ignoreCase = true),
        )
        assertTrue("expected curated eis, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen219_eaPronounNotStubMiss() {
        val v = repo.verse("Gen.2.19")!!
        val ea = v.words.first { it.la.equals("ea", ignoreCase = true) }
        val g = repo.gloss(ea.glossId)!!
        assertTrue(
            "ea should be she/that/them: ${g.primary}",
            g.primary.contains("she", ignoreCase = true) ||
                g.primary.contains("that", ignoreCase = true) ||
                g.primary.contains("them", ignoreCase = true),
        )
        assertTrue("expected curated ea, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not remain stub", ea.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen117_easThemFeminine() {
        val v = repo.verse("Gen.1.17")!!
        val eas = v.words.first { it.la.equals("eas", ignoreCase = true) }
        val g = repo.gloss(eas.glossId)!!
        assertTrue(
            "eas should be them (f.): ${g.primary}",
            g.primary.contains("them", ignoreCase = true) || g.primary.contains("those", ignoreCase = true),
        )
        assertTrue("expected curated eas, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen121_suasOwnNotUrge() {
        val v = repo.verse("Gen.1.21")!!
        val suas = v.words.first { it.la.equals("suas", ignoreCase = true) }
        val g = repo.gloss(suas.glossId)!!
        assertTrue(
            "suas should be his/her/their own: ${g.primary}",
            g.primary.contains("own", ignoreCase = true),
        )
        assertFalse("suas must NEVER mean urge", g.primary.contains("urge", ignoreCase = true))
        assertFalse("suas must NEVER mean recommend", g.primary.contains("recommend", ignoreCase = true))
        assertFalse("suas must NEVER mean advice", g.primary.contains("advice", ignoreCase = true))
        assertTrue("expected curated suas, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:suas (suadeō)", suas.glossId == "w:suas")
    }

    @Test
    fun gen111_suumOwn() {
        val v = repo.verse("Gen.1.11")!!
        val suum = v.words.first { it.la.equals("suum", ignoreCase = true) }
        val g = repo.gloss(suum.glossId)!!
        assertTrue("suum should be own: ${g.primary}", g.primary.contains("own", ignoreCase = true))
        assertTrue("expected curated suum, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen128_eamHer() {
        val v = repo.verse("Gen.1.28")!!
        val eam = v.words.first { it.la.equals("eam", ignoreCase = true) }
        val g = repo.gloss(eam.glossId)!!
        assertTrue(
            "eam should be her/it: ${g.primary}",
            g.primary.contains("her", ignoreCase = true) || g.primary.contains("it", ignoreCase = true),
        )
        assertTrue("expected curated eam, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen223_hocThis() {
        val v = repo.verse("Gen.2.23")!!
        val hoc = v.words.first { it.la.equals("Hoc", ignoreCase = true) }
        val g = repo.gloss(hoc.glossId)!!
        assertTrue("hoc should be this: ${g.primary}", g.primary.contains("this", ignoreCase = true))
        assertFalse("hoc must NEVER mean hockey", g.primary.contains("hockey", ignoreCase = true))
        assertTrue("expected curated hoc, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen129_vobisToForYouPl() {
        val v = repo.verse("Gen.1.29")!!
        val tokens = v.words.filter { it.la.equals("vobis", ignoreCase = true) }
        assertTrue("expected vobis in Gen.1.29", tokens.isNotEmpty())
        tokens.forEach { tok ->
            val g = repo.gloss(tok.glossId)!!
            assertTrue(
                "vobis should be to/for you (pl.): ${g.primary}",
                g.primary.contains("you", ignoreCase = true),
            )
            assertTrue("expected curated vobis, got ${g.id}", g.id.startsWith("curated:"))
        }
    }




    @Test
    fun gen111_sitLetItBeNotAllow() {
        val v = repo.verse("Gen.1.11")!!
        val tokens = v.words.filter { it.la.equals("sit", ignoreCase = true) }
        assertTrue("expected sit in Gen.1.11", tokens.isNotEmpty())
        tokens.forEach { tok ->
            val g = repo.gloss(tok.glossId)!!
            assertTrue(
                "sit should be let it be / may be: ${g.primary}",
                g.primary.contains("let it be", ignoreCase = true) ||
                    g.primary.contains("may be", ignoreCase = true),
            )
            assertFalse("sit must NEVER mean allow", g.primary.contains("allow", ignoreCase = true))
            assertFalse("sit must NEVER mean permit", g.primary.contains("permit", ignoreCase = true))
            assertTrue("expected curated sit, got ${g.id}", g.id.startsWith("curated:"))
            assertFalse("must not bind w:sit (allow)", tok.glossId == "w:sit")
        }
    }

    @Test
    fun gen224_eruntTheyWillBeNotPluck() {
        val v = repo.verse("Gen.2.24")!!
        val erunt = v.words.first { it.la.equals("erunt", ignoreCase = true) }
        val g = repo.gloss(erunt.glossId)!!
        assertTrue(
            "erunt should be they will be: ${g.primary}",
            g.primary.contains("will be", ignoreCase = true) ||
                g.primary.contains("they will", ignoreCase = true),
        )
        assertFalse("erunt must NEVER mean pluck", g.primary.contains("pluck", ignoreCase = true))
        assertFalse("erunt must NEVER mean dig", g.primary.contains("dig", ignoreCase = true))
        assertTrue("expected curated erunt, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:eru (pluck)", erunt.glossId == "w:eru")
    }

    @Test
    fun gen310_essemIWereNotEat() {
        val v = repo.verse("Gen.3.10")!!
        val essem = v.words.first { it.la.equals("essem", ignoreCase = true) }
        val g = repo.gloss(essem.glossId)!!
        assertTrue(
            "essem should be I were / might be: ${g.primary}",
            g.primary.contains("were", ignoreCase = true) ||
                g.primary.contains("might be", ignoreCase = true) ||
                g.primary.contains("I were", ignoreCase = true),
        )
        assertFalse("essem must NEVER mean eat", g.primary.contains("eat", ignoreCase = true))
        assertFalse("essem must NEVER mean consume", g.primary.contains("consume", ignoreCase = true))
        assertTrue("expected curated essem, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:ess (eat)", essem.glossId == "w:ess")
    }

    @Test
    fun gen311_essesYouWereNotEat() {
        val v = repo.verse("Gen.3.11")!!
        val esses = v.words.first { it.la.equals("esses", ignoreCase = true) }
        val g = repo.gloss(esses.glossId)!!
        assertTrue(
            "esses should be you were: ${g.primary}",
            g.primary.contains("were", ignoreCase = true) ||
                g.primary.contains("might be", ignoreCase = true),
        )
        assertFalse("esses must NEVER mean eat", g.primary.contains("eat", ignoreCase = true))
        assertTrue("expected curated esses, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:ess (eat)", esses.glossId == "w:ess")
    }

    @Test
    fun gen14_essetWereFilled() {
        val v = repo.verse("Gen.1.4")!!
        val esset = v.words.first { it.la.equals("esset", ignoreCase = true) }
        val g = repo.gloss(esset.glossId)!!
        assertTrue(
            "esset should be were / might be: ${g.primary}",
            g.primary.contains("were", ignoreCase = true) ||
                g.primary.contains("might be", ignoreCase = true),
        )
        assertFalse("must not remain stub", esset.glossId!!.startsWith("stub:"))
        assertTrue("expected curated esset, got ${g.id}", g.id.startsWith("curated:"))
    }

    @Test
    fun gen114_sintTheyMayBeNotButIf() {
        val v = repo.verse("Gen.1.14")!!
        val sint = v.words.first { it.la.equals("sint", ignoreCase = true) }
        val g = repo.gloss(sint.glossId)!!
        assertTrue(
            "sint should be they may be: ${g.primary}",
            g.primary.contains("may be", ignoreCase = true) ||
                g.primary.contains("let them be", ignoreCase = true),
        )
        assertFalse("sint must NEVER mean but if", g.primary.contains("but if", ignoreCase = true))
        assertTrue("expected curated sint, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:sin (but if)", sint.glossId == "w:sin")
    }

    @Test
    fun gen414_eroIWillBeNotBasket() {
        val v = repo.verse("Gen.4.14")!!
        val ero = v.words.first { it.la.equals("ero", ignoreCase = true) }
        val g = repo.gloss(ero.glossId)!!
        assertTrue(
            "ero should be I will be: ${g.primary}",
            g.primary.contains("will be", ignoreCase = true) ||
                g.primary.contains("I will", ignoreCase = true),
        )
        assertFalse("ero must NEVER mean basket", g.primary.contains("basket", ignoreCase = true))
        assertTrue("expected curated ero, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:ero (basket)", ero.glossId == "w:ero")
    }

    @Test
    fun gen316_erisYouWillBeNotHedgehog() {
        val v = repo.verse("Gen.3.16")!!
        val eris = v.words.first { it.la.equals("eris", ignoreCase = true) }
        val g = repo.gloss(eris.glossId)!!
        assertTrue(
            "eris should be you will be: ${g.primary}",
            g.primary.contains("will be", ignoreCase = true),
        )
        assertFalse("eris must NEVER mean hedgehog", g.primary.contains("hedgehog", ignoreCase = true))
        assertTrue("expected curated eris, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:eris (hedgehog)", eris.glossId == "w:eris")
    }



    // --- v0.1.11 Wave 5: proper names / false friends ---

    @Test
    fun gen1715_saraNotHoe() {
        val v = repo.verse("Gen.17.15")!!
        // Sarai ... Saram in this verse
        val saram = v.words.first { it.la.equals("Saram", ignoreCase = true) }
        val g = repo.gloss(saram.glossId)!!
        assertTrue("Saram should be Sarah: ${g.primary}", g.primary.contains("Sarah", ignoreCase = true) || g.primary.contains("Sara", ignoreCase = true))
        assertFalse("Saram must NEVER mean hoe", g.primary.contains("hoe", ignoreCase = true))
        assertTrue("expected curated, got ${g.id}", g.id.startsWith("curated:"))
        assertFalse("must not bind w:sar (hoe)", saram.glossId == "w:sar")
    }

    @Test
    fun gen1717_saraNotHoe() {
        val v = repo.verse("Gen.17.17")!!
        val sara = v.words.first { it.la.equals("Sara", ignoreCase = true) }
        val g = repo.gloss(sara.glossId)!!
        assertTrue(g.primary.contains("Sarah", ignoreCase = true) || g.primary.contains("Sara", ignoreCase = true))
        assertFalse(g.primary.contains("hoe", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen1127_lotNotWash() {
        val v = repo.verse("Gen.11.27")!!
        val lot = v.words.first { it.la.equals("Lot", ignoreCase = true) }
        val g = repo.gloss(lot.glossId)!!
        assertTrue("Lot should be proper name: ${g.primary}", g.primary.contains("Lot", ignoreCase = true))
        assertFalse("Lot must NEVER mean wash", g.primary.contains("wash", ignoreCase = true))
        assertFalse(g.primary.contains("bathe", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(lot.glossId == "w:lot")
    }

    @Test
    fun gen2530_edomNotSubdue() {
        val v = repo.verse("Gen.25.30")!!
        val edom = v.words.first { it.la.equals("Edom", ignoreCase = true) }
        val g = repo.gloss(edom.glossId)!!
        assertTrue(g.primary.contains("Edom", ignoreCase = true))
        assertFalse(g.primary.contains("subdue", ignoreCase = true))
        assertFalse(g.primary.contains("subjugate", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(edom.glossId == "w:edom")
    }

    @Test
    fun gen1616_sexIsSixNotSex() {
        val v = repo.verse("Gen.16.16")!!
        val sex = v.words.first { it.la.equals("sex", ignoreCase = true) }
        val g = repo.gloss(sex.glossId)!!
        assertTrue("sex should be six: ${g.primary}", g.primary.contains("six", ignoreCase = true))
        assertFalse("primary must not be bare 'sex'", g.primary.trim().equals("sex", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen113_veniteComeNotSale() {
        val v = repo.verse("Gen.11.3")!!
        val venite = v.words.first { it.la.equals("Venite", ignoreCase = true) }
        val g = repo.gloss(venite.glossId)!!
        assertTrue("Venite should be come: ${g.primary}", g.primary.contains("come", ignoreCase = true))
        assertFalse(g.primary.contains("sale", ignoreCase = true))
        assertFalse(g.primary.contains("sold", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(venite.glossId == "w:venit")
    }

    @Test
    fun gen613_venitComeNotSale() {
        val v = repo.verse("Gen.6.13")!!
        val venit = v.words.first { it.la.equals("venit", ignoreCase = true) }
        val g = repo.gloss(venit.glossId)!!
        assertTrue(g.primary.contains("come", ignoreCase = true))
        assertFalse(g.primary.contains("sale", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen1019_adamamAdmahNotLust() {
        val v = repo.verse("Gen.10.19")!!
        val tok = v.words.first { it.la.equals("Adamam", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue("Adamam should be Admah place: ${g.primary}", g.primary.contains("Admah", ignoreCase = true) || g.primary.contains("Adama", ignoreCase = true))
        assertFalse(g.primary.contains("lust", ignoreCase = true))
        assertFalse(g.primary.contains("fall in love", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:adam")
    }

    @Test
    fun gen142_adamaeAdmahNotLust() {
        val v = repo.verse("Gen.14.2")!!
        val tok = v.words.first { it.la.equals("Adamæ", ignoreCase = true) || it.la.equals("Adamae", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("Admah", ignoreCase = true) || g.primary.contains("Adama", ignoreCase = true))
        assertFalse(g.primary.contains("lust", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:adam")
    }

    @Test
    fun gen307_balaNotBleat() {
        val v = repo.verse("Gen.30.7")!!
        val bala = v.words.first { it.la.equals("Bala", ignoreCase = true) }
        val g = repo.gloss(bala.glossId)!!
        assertTrue(g.primary.contains("Bala", ignoreCase = true) || g.primary.contains("Bilhah", ignoreCase = true))
        assertFalse(g.primary.contains("bleat", ignoreCase = true))
        assertFalse(g.primary.contains("baa", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen383_herNotAdhere() {
        val v = repo.verse("Gen.38.3")!!
        val her = v.words.first { it.la.equals("Her", ignoreCase = true) }
        val g = repo.gloss(her.glossId)!!
        assertTrue(g.primary.contains("Her", ignoreCase = true) || g.primary.contains("Er", ignoreCase = true))
        assertFalse(g.primary.contains("adhere", ignoreCase = true))
        assertFalse(g.primary.contains("stick", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen1024_saleNotLeap() {
        val v = repo.verse("Gen.10.24")!!
        val sale = v.words.first { it.la.equals("Sale", ignoreCase = true) }
        val g = repo.gloss(sale.glossId)!!
        assertTrue(g.primary.contains("Sale", ignoreCase = true) || g.primary.contains("Salah", ignoreCase = true))
        assertFalse(g.primary.contains("leap", ignoreCase = true))
        assertFalse(g.primary.contains("jump", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen1418_salemNotLeap() {
        val v = repo.verse("Gen.14.18")!!
        val salem = v.words.first { it.la.equals("Salem", ignoreCase = true) }
        val g = repo.gloss(salem.glossId)!!
        assertTrue(g.primary.contains("Salem", ignoreCase = true))
        assertFalse(g.primary.contains("leap", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }



    // --- v0.1.12 Wave 6: V-over-N mid pack prefer N ---

    @Test
    fun gen71_domusHouseNotSubdue() {
        val v = repo.verse("Gen.7.1")!!
        val tok = v.words.first { it.la.equals("domus", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue("domus should be house: ${g.primary}", g.primary.contains("house", ignoreCase = true) || g.primary.contains("household", ignoreCase = true))
        assertFalse(g.primary.contains("subdue", ignoreCase = true))
        assertFalse(g.primary.contains("tame", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:dom")
    }

    @Test
    fun gen19_locumPlaceNotPlaceVerb() {
        val v = repo.verse("Gen.1.9")!!
        val tok = v.words.first { it.la.equals("locum", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("place", ignoreCase = true))
        assertFalse(g.primary.contains("put", ignoreCase = true))
        assertFalse(g.primary.contains("station", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:loc")
    }

    @Test
    fun gen925_servusServantNotServe() {
        val v = repo.verse("Gen.9.25")!!
        val tok = v.words.first { it.la.equals("servus", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("servant", ignoreCase = true) || g.primary.contains("slave", ignoreCase = true))
        assertFalse(g.primary.trim().equals("serve", ignoreCase = true))
        assertFalse(g.primary.lowercase().startsWith("serve"))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:serv")
    }

    @Test
    fun gen99_pactumCovenantNotCompose() {
        val v = repo.verse("Gen.9.9")!!
        val tok = v.words.first { it.la.equals("pactum", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("covenant", ignoreCase = true) || g.primary.contains("pact", ignoreCase = true))
        assertFalse(g.primary.contains("compose", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:pact")
    }

    @Test
    fun gen47_peccatumSinNounNotVerb() {
        val v = repo.verse("Gen.4.7")!!
        val tok = v.words.first { it.la.equals("peccatum", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("sin", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertTrue(
            "expected noun framing: ${g.primary}",
            g.primary.contains("noun", ignoreCase = true) ||
                g.senses.any { it.contains("sin", ignoreCase = true) }
        )
    }

    @Test
    fun gen410_voxVoiceNotCall() {
        val v = repo.verse("Gen.4.10")!!
        val tok = v.words.first { it.la.equals("vox", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("voice", ignoreCase = true))
        assertFalse(g.primary.contains("call", ignoreCase = true))
        assertFalse(g.primary.contains("summon", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen38_vocemVoiceNotCall() {
        val v = repo.verse("Gen.3.8")!!
        val tok = v.words.first { it.la.equals("vocem", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("voice", ignoreCase = true))
        assertFalse(g.primary.contains("call", ignoreCase = true))
        assertFalse(g.primary.contains("summon", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:voc")
    }

    @Test
    fun gen22_opusWorkNotCover() {
        val v = repo.verse("Gen.2.2")!!
        val tok = v.words.first { it.la.equals("opus", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("work", ignoreCase = true) || g.primary.contains("deed", ignoreCase = true))
        assertFalse(g.primary.contains("cover", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen111_genusKindNotSonInLaw() {
        val v = repo.verse("Gen.1.11")!!
        val tok = v.words.first { it.la.equals("genus", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            g.primary.contains("kind", ignoreCase = true) ||
                g.primary.contains("race", ignoreCase = true) ||
                g.primary.contains("species", ignoreCase = true)
        )
        assertFalse(g.primary.contains("son-in-law", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen1216_bovesOxenNotBellow() {
        val v = repo.verse("Gen.12.16")!!
        val tok = v.words.first { it.la.equals("boves", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("oxen", ignoreCase = true) || g.primary.contains("cattle", ignoreCase = true))
        assertFalse(g.primary.contains("bellow", ignoreCase = true))
        assertFalse(g.primary.contains("roar", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:bov")
    }

    @Test
    fun gen161_ancillamMaidservantNotVerb() {
        val v = repo.verse("Gen.16.1")!!
        val tok = v.words.first { it.la.equals("ancillam", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            g.primary.contains("maidservant", ignoreCase = true) ||
                g.primary.contains("handmaid", ignoreCase = true) ||
                g.primary.contains("maid", ignoreCase = true)
        )
        assertFalse(g.primary.contains("wait on", ignoreCase = true))
        assertFalse(g.primary.contains("hand and foot", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen3913_vestemGarmentNotClothe() {
        val v = repo.verse("Gen.39.13")!!
        val tok = v.words.first { it.la.equals("vestem", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            g.primary.contains("garment", ignoreCase = true) ||
                g.primary.contains("clothing", ignoreCase = true) ||
                g.primary.contains("robe", ignoreCase = true)
        )
        assertFalse(g.primary.contains("clothe", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:vest")
    }

    @Test
    fun gen4334_parsPartNotForbear() {
        val v = repo.verse("Gen.43.34")!!
        val tok = v.words.first { it.la.equals("pars", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("part", ignoreCase = true) || g.primary.contains("portion", ignoreCase = true))
        assertFalse(g.primary.contains("forbear", ignoreCase = true))
        assertFalse(g.primary.trim().equals("bear", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen220_nominibusNamesNotCallVerb() {
        val v = repo.verse("Gen.2.20")!!
        val tok = v.words.first { it.la.equals("nominibus", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("name", ignoreCase = true))
        assertFalse(g.primary.contains("call", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:nomin")
    }

    @Test
    fun gen2817_portaGateNotCarry() {
        val v = repo.verse("Gen.28.17")!!
        val tok = v.words.first { it.la.equals("porta", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("gate", ignoreCase = true) || g.primary.contains("door", ignoreCase = true))
        assertFalse(g.primary.contains("carry", ignoreCase = true))
        assertFalse(g.primary.contains("bring", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:port")
    }

    @Test
    fun gen2414_potumDrinkNotBeAble() {
        val v = repo.verse("Gen.24.14")!!
        val tok = v.words.first { it.la.equals("potum", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("drink", ignoreCase = true))
        assertFalse(g.primary.contains("be able", ignoreCase = true))
        assertFalse(g.primary.trim().equals("can", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:pot")
    }




    // --- v0.1.13 Wave 7: high-value stubs + Gen.4.23 Adæ→Ada ---

    @Test
    fun gen423_adaeIsAdaNotAdam() {
        val v = repo.verse("Gen.4.23")!!
        val tokens = v.words.filter {
            it.la.equals("Adæ", ignoreCase = true) ||
                it.la.equals("Adae", ignoreCase = true) ||
                it.lemmaId == "adae"
        }
        assertTrue("expected Adæ in Gen.4.23", tokens.isNotEmpty())
        for (tok in tokens) {
            val g = repo.gloss(tok.glossId)!!
            assertTrue(
                "Gen.4.23 Adæ should be Ada (Lamech wife): ${g.primary}",
                g.primary.contains("Ada", ignoreCase = true),
            )
            assertFalse(
                "Gen.4.23 Adæ must NOT be Adam: ${g.primary}",
                g.primary.contains("Adam", ignoreCase = true),
            )
            assertFalse(g.primary.contains("plow", ignoreCase = true))
            assertTrue(
                "expected curated:ada, got ${g.id}",
                g.id == "curated:ada" || g.id.startsWith("curated:"),
            )
            assertFalse(tok.glossId!!.startsWith("stub:"))
        }
    }

    @Test
    fun gen220_317_321_adaeStillAdamGenitive() {
        // Regression: Adam genitive verses must stay Adam (not Ada)
        for (id in listOf("Gen.2.20", "Gen.3.17", "Gen.3.21")) {
            val v = repo.verse(id)!!
            val tokens = v.words.filter {
                it.la.equals("Adæ", ignoreCase = true) ||
                    it.la.equals("Adae", ignoreCase = true) ||
                    it.lemmaId == "adae"
            }
            assertTrue("expected Adæ/Adae in $id", tokens.isNotEmpty())
            for (tok in tokens) {
                val g = repo.gloss(tok.glossId)!!
                assertTrue("Adæ should remain Adam (gen.) @ $id: ${g.primary}", g.primary.contains("Adam", ignoreCase = true))
                assertFalse("must not be Ada wife @ $id", g.primary.contains("Lamech", ignoreCase = true))
                assertFalse(g.primary.contains("plow", ignoreCase = true))
                assertEquals("curated:adae", g.id)
            }
        }
    }

    @Test
    fun gen423_sellaeNotChair() {
        val v = repo.verse("Gen.4.23")!!
        val tok = v.words.first {
            it.la.equals("Sellæ", ignoreCase = true) || it.la.equals("Sellae", ignoreCase = true)
        }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            "Sellæ should be Sella: ${g.primary}",
            g.primary.contains("Sella", ignoreCase = true) || g.primary.contains("Zillah", ignoreCase = true),
        )
        assertFalse(g.primary.contains("chair", ignoreCase = true))
        assertFalse(g.primary.contains("seat", ignoreCase = true))
        assertFalse(g.primary.contains("stool", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId == "w:sellar" || tok.glossId == "w:sell")
    }

    @Test
    fun gen419_sellaNotChair() {
        val v = repo.verse("Gen.4.19")!!
        val tok = v.words.first { it.la.equals("Sella", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("Sella", ignoreCase = true) || g.primary.contains("Zillah", ignoreCase = true))
        assertFalse(g.primary.contains("chair", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
    }

    @Test
    fun gen124_suoOwnNotStub() {
        val v = repo.verse("Gen.1.24")!!
        val tok = v.words.first { it.la.equals("suo", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue("suo should be own: ${g.primary}", g.primary.contains("own", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen112_suamOwnNotStub() {
        val v = repo.verse("Gen.1.12")!!
        val tok = v.words.first { it.la.equals("suam", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("own", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen314_tuumYourNotStub() {
        val v = repo.verse("Gen.3.14")!!
        val tok = v.words.first { it.la.equals("tuum", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            "tuum should be your: ${g.primary}",
            g.primary.contains("your", ignoreCase = true) || g.primary.contains("thy", ignoreCase = true),
        )
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen122_dicensSayingNotStub() {
        val v = repo.verse("Gen.1.22")!!
        val tok = v.words.first { it.la.equals("dicens", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("saying", ignoreCase = true) || g.primary.contains("speak", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen32_responditAnsweredNotStub() {
        val v = repo.verse("Gen.3.2")!!
        val tok = v.words.first { it.la.equals("respondit", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("answer", ignoreCase = true) || g.primary.contains("repli", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen15_unusOneNotStub() {
        val v = repo.verse("Gen.1.5")!!
        val tok = v.words.first { it.la.equals("unus", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("one", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen372_josephProperNameNotStub() {
        val v = repo.verse("Gen.37.2")!!
        val tok = v.words.first { it.la.equals("Joseph", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("Joseph", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen175_abrahamProperNameNotStub() {
        val v = repo.verse("Gen.17.5")!!
        val tok = v.words.first { it.la.equals("Abraham", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("Abraham", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen33_nobisUsNotStub() {
        val v = repo.verse("Gen.3.3")!!
        val tok = v.words.first { it.la.equals("nobis", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(g.primary.contains("us", ignoreCase = true))
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
    }

    @Test
    fun gen37_seReflexiveNotStub() {
        val v = repo.verse("Gen.3.7")!!
        val tok = v.words.first { it.la.equals("se", ignoreCase = true) }
        val g = repo.gloss(tok.glossId)!!
        assertTrue(
            g.primary.contains("himself", ignoreCase = true) ||
                g.primary.contains("herself", ignoreCase = true) ||
                g.primary.contains("themselves", ignoreCase = true) ||
                g.primary.contains("oneself", ignoreCase = true),
        )
        assertTrue(g.id.startsWith("curated:"))
        assertFalse(tok.glossId!!.startsWith("stub:"))
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
