import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  onNewTarget: (callback: () => void) => {
    ipcRenderer.on('menu:new-target', callback)
    return () => ipcRenderer.removeListener('menu:new-target', callback)
  },
  onSettings: (callback: () => void) => {
    ipcRenderer.on('menu:settings', callback)
    return () => ipcRenderer.removeListener('menu:settings', callback)
  },
  onApprove: (callback: () => void) => {
    ipcRenderer.on('menu:approvals', callback)
    return () => ipcRenderer.removeListener('menu:approvals', callback)
  },
  onAbout: (callback: () => void) => {
    ipcRenderer.on('menu:about', callback)
    return () => ipcRenderer.removeListener('menu:about', callback)
  },
  onUpdateAvailable: (callback: () => void) => {
    ipcRenderer.on('update:available', callback)
    return () => ipcRenderer.removeListener('update:available', callback)
  },
  onUpdateDownloaded: (callback: () => void) => {
    ipcRenderer.on('update:downloaded', callback)
    return () => ipcRenderer.removeListener('update:downloaded', callback)
  },
  installUpdate: () => {
    ipcRenderer.send('update:install')
  },
  platform: process.platform,
})
