export default {
  local: {
    get(key, default_) {
      let item_str = localStorage.getItem(key);
      if (item_str)
        return JSON.parse(item_str);
      return default_;
    },
    set(key, value) {
      let item_str = JSON.stringify(value);
      localStorage.setItem(key, item_str);
    },
    remove(key) {
      localStorage.removeItem(key);
    },
    clear() {
      localStorage.clear();
    }
  },
  session: {
    get(key) {
      let item_str = sessionStorage.getItem(key);
      if (item_str) {
        return JSON.parse(item_str);
      }
    },
    set(key, value) {
      let item_str = JSON.stringify(value);
      sessionStorage.setItem(key, item_str);
    },
    remove(key) {
      sessionStorage.removeItem(key);
    },
    clear() {
      sessionStorage.clear();
    }
  }
}
