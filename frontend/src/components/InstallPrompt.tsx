import { useEffect, useState } from 'react'
import { Download, X } from 'lucide-react'

// The browser's beforeinstallprompt event (not in the standard TS lib types).
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISS_KEY = 'dad-install-dismissed'

/**
 * Shows a small "Install app" banner on Android/Chrome when the PWA is installable.
 * Hidden when already installed (standalone) or previously dismissed.
 */
export default function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const isStandalone =
      window.matchMedia('(display-mode: standalone)').matches ||
      // iOS Safari
      (window.navigator as unknown as { standalone?: boolean }).standalone === true
    if (isStandalone || localStorage.getItem(DISMISS_KEY) === '1') return

    const onPrompt = (e: Event) => {
      e.preventDefault()
      setDeferred(e as BeforeInstallPromptEvent)
      setVisible(true)
    }
    const onInstalled = () => setVisible(false)

    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  if (!visible || !deferred) return null

  const install = async () => {
    await deferred.prompt()
    await deferred.userChoice
    setVisible(false)
    setDeferred(null)
  }

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, '1')
    setVisible(false)
  }

  return (
    <div className="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center gap-3 rounded-xl border border-indigo-200 bg-white p-3 shadow-lg sm:left-auto sm:right-4 dark:border-indigo-900 dark:bg-neutral-900">
      <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg bg-indigo-600 text-white">
        <Download className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">Install Dad</p>
        <p className="truncate text-xs text-neutral-500 dark:text-neutral-400">
          Add to your home screen for quick access.
        </p>
      </div>
      <button
        onClick={install}
        className="flex-none rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
      >
        Install
      </button>
      <button
        onClick={dismiss}
        aria-label="Dismiss"
        className="flex-none rounded-md p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
