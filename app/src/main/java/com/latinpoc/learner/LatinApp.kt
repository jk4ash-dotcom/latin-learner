package com.latinpoc.learner

import android.app.Application
import com.latinpoc.learner.data.PackRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class LatinApp : Application() {
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private val _repository = MutableStateFlow<PackRepository?>(null)
    val repository: StateFlow<PackRepository?> = _repository.asStateFlow()

    private val _loadError = MutableStateFlow<String?>(null)
    val loadError: StateFlow<String?> = _loadError.asStateFlow()

    override fun onCreate() {
        super.onCreate()
        appScope.launch {
            runCatching { PackRepository.load(this@LatinApp) }
                .onSuccess { repo ->
                    _repository.value = repo
                    launch {
                        runCatching { repo.ensureGlosses() }
                    }
                }
                .onFailure { _loadError.value = it.message ?: "Failed to load pack" }
        }
    }

    companion object {
        fun from(context: android.content.Context): LatinApp =
            context.applicationContext as LatinApp
    }
}
