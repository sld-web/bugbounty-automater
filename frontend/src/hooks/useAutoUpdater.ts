import { useEffect } from 'react'

declare global {
  interface Window {
    electronAPI?: {
      onNewTarget: (callback: () => void) => () => void
      onSettings: (callback: () => void) => () => void
      onApprove: (callback: () => void) => () => void
      onAbout: (callback: () => void) => () => void
      onUpdateAvailable: (callback: () => void) => () => void
      onUpdateDownloaded: (callback: () => void) => () => void
      installUpdate: () => void
      platform: string
    }
  }
}

export function useAutoUpdater() {
  useEffect(() => {
    if (!window.electronAPI) return

    const unsubAvailable = window.electronAPI.onUpdateAvailable(() => {
      console.log('Update available')
    })

    const unsubDownloaded = window.electronAPI.onUpdateDownloaded(() => {
      console.log('Update downloaded - restart to install')
    })

    return () => {
      unsubAvailable()
      unsubDownloaded()
    }
  }, [])
}
