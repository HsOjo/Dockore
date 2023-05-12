import Loading from "element-ui/packages/loading/src";
import Notification from "element-ui/packages/notification/src/main";
import isElectron from "is-electron";

let loadings = [], loading;
let debounce_timeout = {}

export default {
  startLoading(text) {
    loadings.push({text, lock: true});
    if (loadings.length && !loading) {
      loading = Loading(loadings.pop());
      loading.$el.style['z-index'] = 9999;
    }
  },
  stopLoading() {
    loading.close();
    if (loadings.length) {
      loading = Loading(loadings.pop());
    } else {
      loading = undefined;
    }
  },
  sendNotification(title, message, type, html, duration, offset) {
    offset |= 16;
    duration |= 3;
    duration *= 1000;
    if (html === undefined)
      html = true;
    if (html)
      message = message.replace('\n', '<br>');
    Notification({title, message, type, offset, duration, dangerouslyUseHTMLString: html, position: 'bottom-right'})
  },
  copyObject(obj) {
    return JSON.parse(JSON.stringify(obj));
  },
  debounce(fn, wait) {
    if (debounce_timeout[fn]) clearTimeout(debounce_timeout[fn])
    debounce_timeout[fn] = setTimeout(fn, wait)
  },
  getElectron() {
    if (!isElectron())
      return null
    return window.require('electron')
  }
}
