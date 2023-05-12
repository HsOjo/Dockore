import Vue from 'vue'
import helper from "@/utils/helper";
import store from "@/store";

let URL;
let URL_KEY_MAPPING = {}

function getBaseURL() {
  let url;
  let info = store.getters.serverInfo
  if (info)
    url = `${info.ssl ? 'https' : 'http'}://${info.host}`;
  else
    url = `${import.meta.VITE_APP_BASE_URL}`

  return url;
}

function getWSURL() {
  let url;
  let info = store.getters.serverInfo
  if (info)
    url = `${info.ssl ? 'wss' : 'ws'}://${info.host_ws}`;
  else
    url = `${import.meta.VITE_APP_WS_URL}`

  return url;
}

function generateURL() {
  let root = `${getBaseURL()}/api`;

  URL = {
    ADMIN_SYSTEM_CONFIG: `${root}/admin/system/config`,

    ADMIN_USER_LIST: `${root}/admin/user/list`,
    ADMIN_USER_ITEM: `${root}/admin/user/item`,
    ADMIN_USER_ADD: `${root}/admin/user/add`,
    ADMIN_USER_EDIT: `${root}/admin/user/edit`,
    ADMIN_USER_DELETE: `${root}/admin/user/delete`,
    ADMIN_USER_REMOVE_OWNER_SHIP: `${root}/admin/user/remove-owner-ship`,
    ADMIN_USER_DISTRIBUTE_OBJECT: `${root}/admin/user/distribute-object`,

    SYSTEM_VERSION: `${root}/system/version`,

    USER_LOGIN: `${root}/user/login`,
    USER_INFO: `${root}/user/info`,
    USER_CHANGE_PASSWORD: `${root}/user/change-password`,

    IMAGE_LIST: `${root}/image/list`,
    IMAGE_ITEM: `${root}/image/item`,
    IMAGE_DELETE: `${root}/image/delete`,
    IMAGE_SEARCH: `${root}/image/search`,
    IMAGE_PULL: `${root}/image/pull`,
    IMAGE_TAG: `${root}/image/tag`,
    IMAGE_HISTORY: `${root}/image/history`,

    CONTAINER_LIST: `${root}/container/list`,
    CONTAINER_ITEM: `${root}/container/item`,
    CONTAINER_DELETE: `${root}/container/delete`,
    CONTAINER_CREATE: `${root}/container/create`,
    CONTAINER_RUN: `${root}/container/run`,
    CONTAINER_START: `${root}/container/start`,
    CONTAINER_STOP: `${root}/container/stop`,
    CONTAINER_RESTART: `${root}/container/restart`,
    CONTAINER_RENAME: `${root}/container/rename`,
    CONTAINER_LOGS: `${root}/container/logs`,
    CONTAINER_DIFF: `${root}/container/diff`,
    CONTAINER_COMMIT: `${root}/container/commit`,
    CONTAINER_TERMINAL: `${root}/container/terminal`,

    NETWORK_LIST: `${root}/network/list`,
    NETWORK_ITEM: `${root}/network/item`,
    NETWORK_DELETE: `${root}/network/delete`,
    NETWORK_CREATE: `${root}/network/create`,
    NETWORK_CONNECT: `${root}/network/connect`,
    NETWORK_DISCONNECT: `${root}/network/disconnect`,

    VOLUME_LIST: `${root}/volume/list`,
    VOLUME_ITEM: `${root}/volume/item`,
    VOLUME_DELETE: `${root}/volume/delete`,
    VOLUME_CREATE: `${root}/volume/create`,
  }

  for (let [k, v] of Object.entries(URL))
    URL_KEY_MAPPING[v] = k;
}

let options = {
  ADMIN_SYSTEM_CONFIG: {name: '系统设置'},

  ADMIN_USER_ADD: {name: '添加用户'},
  ADMIN_USER_EDIT: {name: '编辑用户'},
  ADMIN_USER_DELETE: {name: '删除用户'},
  ADMIN_USER_REMOVE_OWNER_SHIP: {name: '移除所有权'},
  ADMIN_USER_DISTRIBUTE_OBJECT: {name: '分配对象'},

  USER_LOGIN: {name: '用户登录'},
  USER_INFO: {name: '获取用户信息', notify: false},
  USER_CHANGE_PASSWORD: {name: '修改密码'},

  IMAGE_PULL: {name: '拉取镜像'},
  IMAGE_DELETE: {name: '删除镜像'},
  IMAGE_SEARCH: {name: '搜索线上镜像', notify: false},
  IMAGE_TAG: {name: '标记镜像'},
  IMAGE_HISTORY: {name: '获取镜像历史记录', notify: false},

  CONTAINER_CREATE: {name: '创建容器'},
  CONTAINER_DELETE: {name: '删除容器'},
  CONTAINER_RUN: {name: '运行容器'},
  CONTAINER_START: {name: '启动容器'},
  CONTAINER_STOP: {name: '停止容器'},
  CONTAINER_RESTART: {name: '重启容器'},
  CONTAINER_RENAME: {name: '容器更名'},
  CONTAINER_LOGS: {name: '获取容器日志', notify: false},
  CONTAINER_DIFF: {name: '容器差异对比', notify: false},
  CONTAINER_COMMIT: {name: '提交容器镜像'},

  NETWORK_CREATE: {name: '创建网络'},
  NETWORK_DELETE: {name: '删除网络'},
  NETWORK_CONNECT: {name: '连接网络'},
  NETWORK_DISCONNECT: {name: '断开网络'},

  VOLUME_CREATE: {name: '创建存储卷'},
  VOLUME_DELETE: {name: '删除存储卷'},
}

let axios = (new Vue()).$axios;

export default {
  $url: URL,
  $action: {
    getBaseURL,
    getWSURL,
    generateURL,
  },
  $options: (url, method) => {
    let k = URL_KEY_MAPPING[url];
    if (!k)
      for (let kk in URL_KEY_MAPPING)
        if (url.indexOf(kk) !== -1)
          k = URL_KEY_MAPPING[kk];

    let r = {}
    if (k && options[k])
      r = helper.copyObject(options[k]);
    if (r.loading === undefined)
      r.loading = true;
    if (r.notify === undefined)
      r.notify = !!r.name && method !== 'get';

    return r;
  },
  adminQueryConfig: () => axios.get(URL.ADMIN_SYSTEM_CONFIG),
  adminUpdateConfig: (config) => axios.post(URL.ADMIN_SYSTEM_CONFIG, {config}),
  adminUserList: (page, per_page, keyword) => axios.get(
    URL.ADMIN_USER_LIST, {params: {page, per_page, keyword}}),
  adminUserItem: (id) => axios.get(`${URL.ADMIN_USER_ITEM}/${id}`),
  adminUserAdd: (username, password, role_type) => axios.post(URL.ADMIN_USER_ADD, {username, password, role_type}),
  adminUserEdit: (id, username, password, role_type) => axios.post(
    URL.ADMIN_USER_EDIT, {id, username, password, role_type}),
  adminUserDelete: ids => axios.post(URL.ADMIN_USER_DELETE, {ids}),
  adminUserRemoveOwnerShip: ids => axios.post(URL.ADMIN_USER_REMOVE_OWNER_SHIP, {ids}),
  adminUserDistributeObject: (id, type, obj_id) => axios.post(URL.ADMIN_USER_DISTRIBUTE_OBJECT, {id, type, obj_id}),

  queryVersion: () => axios.get(URL.SYSTEM_VERSION),

  userLogin: (username, password) => axios.post(URL.USER_LOGIN, {username, password}),
  userInfo: () => axios.get(URL.USER_INFO),
  userChangePassword: (old, new_) => axios.post(URL.USER_CHANGE_PASSWORD, {old, 'new': new_}),

  imageList: is_all => axios.get(URL.IMAGE_LIST, {params: {is_all}}),
  imageItem: id => axios.get(`${URL.IMAGE_ITEM}/${id}`),
  imageDelete: (ids, tag_only) => axios.post(URL.IMAGE_DELETE, {ids, tag_only}),
  imageSearch: keyword => axios.get(`${URL.IMAGE_SEARCH}/${keyword}`),
  imagePull: (name, tag) => axios.post(URL.IMAGE_PULL, {name, tag}),
  imageTag: (id, name, tag) => axios.post(URL.IMAGE_TAG, {id, name, tag}),
  imageHistory: id => axios.get(`${URL.IMAGE_HISTORY}/${id}`),

  containerList: is_all => axios.get(URL.CONTAINER_LIST, {params: {is_all}}),
  containerItem: id => axios.get(`${URL.CONTAINER_ITEM}/${id}`),
  containerDelete: ids => axios.post(URL.CONTAINER_DELETE, {ids}),
  containerCreate: (image, command, name, interactive, tty, ports, volumes) => axios.post(
    URL.CONTAINER_CREATE, {image, command, name, interactive, tty, ports, volumes}),
  containerRun: (image, command, name, interactive, tty, ports, volumes) => axios.post(
    URL.CONTAINER_RUN, {image, command, name, interactive, tty, ports, volumes}),
  containerStart: ids => axios.post(URL.CONTAINER_START, {ids}),
  containerStop: (ids, timeout) => axios.post(URL.CONTAINER_STOP, {ids, timeout}),
  containerRestart: (ids, timeout) => axios.post(URL.CONTAINER_RESTART, {ids, timeout}),
  containerRename: (id, name) => axios.post(URL.CONTAINER_RENAME, {id, name}),
  containerLogs: (id, since, until) => axios.post(URL.CONTAINER_LOGS, {id, since, until}),
  containerDiff: id => axios.get(`${URL.CONTAINER_DIFF}/${id}`),
  containerCommit: (id, name, tag, message, author) => axios.post(
    URL.CONTAINER_COMMIT, {id, name, tag, message, author}),
  containerTerminal: (id, command) => axios.post(`${URL.CONTAINER_TERMINAL}`, {id, command}),

  volumeList: () => axios.get(URL.VOLUME_LIST),
  volumeItem: id => axios.get(`${URL.VOLUME_ITEM}/${id}`),
  volumeDelete: ids => axios.post(URL.VOLUME_DELETE, {ids}),
  volumeCreate: (name, driver, driver_opts) => axios.post(URL.VOLUME_CREATE, {name, driver, driver_opts}),

  networkList: () => axios.get(URL.NETWORK_LIST),
  networkItem: id => axios.get(`${URL.NETWORK_ITEM}/${id}`),
  networkDelete: ids => axios.post(URL.NETWORK_DELETE, {ids}),
  networkCreate: (name, driver, options, attachable, subnet, gateway, ip_range) => axios.post(
    URL.NETWORK_CREATE, {name, driver, options, attachable, subnet, gateway, ip_range}),
  networkConnect: (id, container_id, ipv4_address) => axios.post(URL.NETWORK_CONNECT, {id, container_id, ipv4_address}),
  networkDisconnect: (id, container_id, force) => axios.post(URL.NETWORK_DISCONNECT, {id, container_id, force}),
}
