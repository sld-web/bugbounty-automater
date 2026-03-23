import { contextBridge as t, ipcRenderer as n } from "electron";
t.exposeInMainWorld("electronAPI", {
  onNewTarget: (e) => (n.on("menu:new-target", e), () => n.removeListener("menu:new-target", e)),
  onSettings: (e) => (n.on("menu:settings", e), () => n.removeListener("menu:settings", e)),
  onApprove: (e) => (n.on("menu:approvals", e), () => n.removeListener("menu:approvals", e)),
  onAbout: (e) => (n.on("menu:about", e), () => n.removeListener("menu:about", e)),
  onUpdateAvailable: (e) => (n.on("update:available", e), () => n.removeListener("update:available", e)),
  onUpdateDownloaded: (e) => (n.on("update:downloaded", e), () => n.removeListener("update:downloaded", e)),
  installUpdate: () => {
    n.send("update:install");
  },
  platform: process.platform
});
