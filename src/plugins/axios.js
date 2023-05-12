"use strict";

import Vue from 'vue';
import axios from "axios";
import storage from '@/utils/storage'
import helper from "@/utils/helper";

// Full config:  https://github.com/axios/axios#request-config
// axios.defaults.baseURL = process.env.baseURL || process.env.apiUrl || '';
// axios.defaults.headers.common['Authorization'] = AUTH_TOKEN;
axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded';

let config = {
  // baseURL: process.env.baseURL || process.env.apiUrl || ""
  // timeout: 60 * 1000, // Timeout
  withCredentials: false, // Check cross-site Access-Control
};

const _axios = axios.create(config);

_axios.interceptors.request.use(
    function (config) {
      // Do something before request is sent
      let token = storage.local.get('user_token')
      if (token)
        config.headers.Authorization = token;

      let options = Vue.prototype.$api.$options(config.url);
      if (options && options.loading)
        helper.startLoading(`${options.name || '加载'}中...`)

      return config;
    },
    function (error) {
      // Do something with request error
      return Promise.reject(error);
    }
);

// Add a response interceptor
_axios.interceptors.response.use(
    function (response) {
      // Do something with response data
      if (import.meta.env.DEV)
        console.log('Resp:', response.data);

      let resp = response.data;
      let success = resp.code === 0;

      let options = Vue.prototype.$api.$options(response.config.url, response.config.method);
      if (options && options.loading)
        helper.stopLoading();

      if (!success || options.notify) {
        let title = options.name;
        if (!title)
          title = success ? '操作成功' : '操作失败';

        let msg = resp.msg;
        let exc = '';
        if (resp.data && (resp.data.exc || resp.data.excs)) {
          if (resp.data.exc)
            exc = resp.data.exc;
          if (resp.data.excs) {
            let excs = resp.data.excs;
            if (excs instanceof Object)
              excs = Object.values(excs);
            if (excs instanceof Array)
              if (excs.length === 1)
                exc = excs[0];
              else if (excs.length > 1)
                exc = `（发生"${excs.length}"个异常）`;
          }
        }

        if (resp.code === -404){
          history.back();
        }

        msg = `<div>${msg}</div><div style="word-break: break-all;">${exc}</div>`;

        helper.sendNotification(title, msg,
            success ? 'success' : 'error',
            true,
            success ? 3 : 10
        );
      }

      return resp;
    },
    function (error) {
      // Do something with response error
      if (import.meta.env.DEV)
        console.log('Error:', error);

      let title = '网络错误';
      if (error.config && error.config.url) {
        let options = Vue.prototype.$api.$options(error.config.url);
        if (options && options.loading)
          helper.stopLoading();

        if (options.name)
          title = options.name;
      }

      helper.sendNotification(title, `<p style="word-break: break-all">${error}</p>`, 'error', true)

      return {code: -1, msg: error};
    }
);

Plugin.install = function (Vue, options) {
  Vue.axios = _axios;
  window.axios = _axios;
  Object.defineProperties(Vue.prototype, {
    axios: {
      get() {
        return _axios;
      }
    },
    $axios: {
      get() {
        return _axios;
      }
    },
  });
};

Vue.use(Plugin)

export default Plugin;
