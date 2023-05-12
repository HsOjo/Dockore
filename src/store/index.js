import Vue from 'vue'
import Vuex from 'vuex'
import storage from '@/utils/storage'
import constant from '@/utils/constant'
import isElectron from "is-electron";

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    is_electron: isElectron(),
    user_token: '',
    user_info: null,
    server_info: null,
  },
  mutations: {
    setUserToken(state, token) {
      state.user_token = token;
      storage.local.set('user_token', token);
    },
    setUserInfo(state, user_info) {
      state.user_info = user_info;
      storage.local.set('user_info', user_info);
    },
    setServerInfo(state, server_info) {
      state.server_info = server_info;
      storage.local.set(constant.global.storage.SERVER_INFO, server_info)
    },
    logout(state) {
      state.user_token = '';
      state.user_info = {};
      storage.local.remove('user_token');
      storage.local.remove('user_info');
    },
  },
  actions: {},
  modules: {},
  getters: {
    userToken(state) {
      let token = state.user_token;
      if (!token)
        token = storage.local.get('user_token');

      return token;
    },
    userInfo(state) {
      let user_info = state.user_info;
      if (!user_info)
        user_info = storage.local.get('user_info');

      return user_info;
    },
    serverInfo(state) {
      let server_info = state.server_info;
      if (!server_info)
        server_info = storage.local.get('server_info');

      return server_info;
    },
    isAdmin(state, getters) {
      let user_info = getters.userInfo;
      if (user_info && user_info.role_type !== undefined)
        return user_info.role_type === constant.role.TYPE_ADMIN;
      return false;
    },
    username(state, getters) {
      return getters.userInfo && getters.userInfo.username
    },
    isElectron(state, getters) {
      return state.is_electron
    },
    isLogined(state, getters) {
      return !!getters.username
    },
    isMac(state, getters) {
      return getters.isElectron && process.platform === 'darwin'
    },
  }
})
