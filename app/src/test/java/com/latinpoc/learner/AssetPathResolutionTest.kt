package com.latinpoc.learner

import com.latinpoc.learner.data.PackRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.FileNotFoundException
import java.io.IOException
import java.util.zip.GZIPOutputStream

class AssetPathResolutionTest {

    @Test
    fun assetCandidates_prefersGzThenPlain_dedupes() {
        val c = PackRepository.assetCandidates(
            "data/glosses.json.gz",
            "data/glosses.json",
            "glosses.json.gz",
            "data/glosses.json.gz",
            null,
            "  "
        )
        assertEquals(
            listOf("data/glosses.json.gz", "data/glosses.json"),
            c
        )
    }

    @Test
    fun readAssetText_fallsBackWhenGzMissing_plainJson() {
        val files = mapOf("data/glosses.json" to """{"w:deus":{"id":"w:deus","primary":"God"}}""")
        val text = PackRepository.readAssetText(
            { path ->
                files[path]?.byteInputStream()
                    ?: throw FileNotFoundException(path)
            },
            "data/glosses.json.gz",
            "data/glosses.json"
        )
        assertTrue(text.contains("w:deus"))
    }

    @Test
    fun readAssetText_readsGzipMagic() {
        val payload = """{"ok":true}"""
        val gz = ByteArrayOutputStream().use { bos ->
            GZIPOutputStream(bos).use { it.write(payload.toByteArray(Charsets.UTF_8)) }
            bos.toByteArray()
        }
        val text = PackRepository.readAssetText(
            { ByteArrayInputStream(gz) },
            "data/glosses.json.gz"
        )
        assertEquals(payload, text)
    }

    @Test
    fun readAssetText_allMissing_listsTriedPaths() {
        try {
            PackRepository.readAssetText(
                { throw FileNotFoundException(it) },
                "data/glosses.json.gz",
                "data/glosses.json"
            )
            fail("expected IOException")
        } catch (e: IOException) {
            assertTrue(e.message!!.contains("data/glosses.json.gz"))
            assertTrue(e.message!!.contains("data/glosses.json"))
        }
    }
}
