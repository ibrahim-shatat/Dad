// Appended to android/build.gradle.kts by CI.
// Flutter compiles each plugin module against its own default SDK (34), regardless of the
// app's compileSdk. file_picker's flutter_plugin_android_lifecycle now requires compiling
// against SDK 36, and firebase requires min SDK 23 — so force both on every Android module
// (the app and all plugins). Uses reflection so no Android Gradle Plugin imports are needed.
subprojects {
    afterEvaluate {
        val android = extensions.findByName("android") ?: return@afterEvaluate
        fun callInt(target: Any, name: String, value: Int) {
            target.javaClass.methods.firstOrNull {
                it.name == name && it.parameterTypes.size == 1 &&
                    (it.parameterTypes[0] == Integer.TYPE || it.parameterTypes[0] == Int::class.java)
            }?.invoke(target, value)
        }
        callInt(android, "compileSdkVersion", 36)
        runCatching {
            val defaultConfig = android.javaClass.getMethod("getDefaultConfig").invoke(android)
            callInt(defaultConfig, "minSdkVersion", 23)
        }
    }
}
