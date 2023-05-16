import {BrowserWindow, ipcMain} from 'electron'

ipcMain.on('minimize', () => {
  let window = BrowserWindow.getFocusedWindow()
  window.minimize()
})

ipcMain.on('is_maximized', (event) => {
  let window = BrowserWindow.getFocusedWindow()
  event.returnValue = window.isMaximized()
})

ipcMain.on('maximize', () => {
  let window = BrowserWindow.getFocusedWindow()
  window.maximize()
})

ipcMain.on('unmaximize', () => {
  let window = BrowserWindow.getFocusedWindow()
  window.unmaximize()
})

ipcMain.on('close', () => {
  let window = BrowserWindow.getFocusedWindow()
  window.close()
})
