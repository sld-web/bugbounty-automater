import { app as o, ipcMain as h, BrowserWindow as d, nativeImage as g, Tray as f, Menu as u } from "electron";
import y from "electron-updater";
import c from "electron-log";
import r from "path";
import { fileURLToPath as m } from "url";
const { autoUpdater: a } = y, k = m(import.meta.url), n = r.dirname(k);
c.initialize();
a.logger = c;
const i = process.env.NODE_ENV === "development" || !o.isPackaged;
let e = null, t = null;
function b() {
  e = new d({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    backgroundColor: "#0c0e14",
    webPreferences: {
      preload: r.join(n, "preload.js"),
      contextIsolation: !0,
      nodeIntegration: !1
    },
    icon: r.join(n, "../public/icon.png"),
    show: !1
  }), e.once("ready-to-show", () => {
    e == null || e.show();
  }), i ? (e.loadURL("http://localhost:5173"), process.env.OPEN_DEVTOOLS === "true" && e.webContents.openDevTools()) : e.loadFile(r.join(n, "../dist/index.html")), e.on("closed", () => {
    e = null;
  }), e.on("minimize", (s) => {
    t && (s.preventDefault(), e == null || e.hide());
  }), T();
}
function T() {
  const s = [
    {
      label: "File",
      submenu: [
        {
          label: "New Target",
          accelerator: "CmdOrCtrl+N",
          click: () => e == null ? void 0 : e.webContents.send("menu:new-target")
        },
        { type: "separator" },
        {
          label: "Settings",
          accelerator: "CmdOrCtrl+,",
          click: () => e == null ? void 0 : e.webContents.send("menu:settings")
        },
        { type: "separator" },
        { role: "quit" }
      ]
    },
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" }
      ]
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" }
      ]
    },
    {
      label: "Window",
      submenu: [
        { role: "minimize" },
        { role: "close" },
        { type: "separator" },
        {
          label: "Always on Top",
          type: "checkbox",
          checked: !1,
          click: (p) => {
            e == null || e.setAlwaysOnTop(p.checked);
          }
        }
      ]
    },
    {
      label: "Help",
      submenu: [
        {
          label: "Documentation",
          click: () => {
            require("electron").shell.openExternal("https://docs.bugbounty.local");
          }
        },
        {
          label: "Check for Updates",
          click: () => {
            a.checkForUpdates();
          }
        },
        { type: "separator" },
        {
          label: "About",
          click: () => {
            e == null || e.webContents.send("menu:about");
          }
        }
      ]
    }
  ], l = u.buildFromTemplate(s);
  u.setApplicationMenu(l);
}
function C() {
  const s = i ? r.join(n, "../public/icon.png") : r.join(process.resourcesPath, "public/icon.png");
  try {
    const l = g.createFromPath(s);
    if (l.isEmpty()) {
      console.log("Tray icon empty, skipping tray creation");
      return;
    }
    t = new f(l);
    const p = u.buildFromTemplate([
      {
        label: "Show Window",
        click: () => {
          e == null || e.show();
        }
      },
      {
        label: "New Target",
        click: () => {
          e == null || e.show(), e == null || e.webContents.send("menu:new-target");
        }
      },
      { type: "separator" },
      {
        label: "Pending Approvals",
        click: () => {
          e == null || e.show(), e == null || e.webContents.send("menu:approvals");
        }
      },
      { type: "separator" },
      {
        label: "Quit",
        click: () => {
          o.quit();
        }
      }
    ]);
    t.setToolTip("BugBounty Automator"), t.setContextMenu(p), t.on("double-click", () => {
      e == null || e.show();
    });
  } catch (l) {
    console.log("Tray creation skipped:", l);
  }
}
a.on("update-available", () => {
  c.info("Update available"), e == null || e.webContents.send("update:available");
});
a.on("update-downloaded", () => {
  c.info("Update downloaded"), e == null || e.webContents.send("update:downloaded");
});
h.on("update:install", () => {
  a.quitAndInstall();
});
o.whenReady().then(() => {
  b(), C(), o.on("activate", () => {
    d.getAllWindows().length === 0 && b();
  }), i || a.checkForUpdatesAndNotify();
});
o.on("window-all-closed", () => {
  process.platform !== "darwin" && o.quit();
});
o.on("before-quit", () => {
  t == null || t.destroy();
});
