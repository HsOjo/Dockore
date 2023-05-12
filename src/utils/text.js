export default {
  global: {
    project: {
      name: 'Dockore',
    },
    route_title: {
      ADMIN_SYSTEM_CONFIG: '系统设置',
      ADMIN_USER: '用户管理',
      ADMIN_USER_ADD: '添加用户',
      ADMIN_USER_EDIT: '编辑用户',
      SYSTEM_VERSION: '系统版本',
      IMAGE: '镜像管理',
      IMAGE_INFO: '镜像信息',
      CONTAINER: '容器管理',
      CONTAINER_INFO: '容器信息',
      CONTAINER_TERMINAL: '容器终端',
      USER_LOGIN: '用户登录',
      VOLUME: '存储卷管理',
      VOLUME_INFO: '存储卷信息',
      NETWORK: '网络管理',
      NETWORK_INFO: '网络信息',
    }
  },
  config: {
    database: {
      this: '数据库设置',
      driver: '驱动',
      host: '主机',
      port: '端口',
      user: '用户名',
      password: '密码',
      database: '数据库',
      charset: '编码',
      echo_sql: '输出SQL',
      path: '路径',
      track_modifications: '追踪变化',
    },
    docker: {
      this: 'Docker设置',
      url: '服务URL',
      cli_bin: '客户端路径',
      terminal_expires: '交互会话有效期',
    },
    user: {
      this: '用户设置',
      login_expires: '登录过期时间',
    },
    flask: {
      this: 'Flask设置',
      SQLALCHEMY_TRACK_MODIFICATIONS: 'SQLAlchemy变更追踪',
      SECRET_KEY: '数据加密密钥',
      WTF_CSRF_ENABLED: '表单CSRF验证',
    },
  },
  version: {
    _: {
      version: '版本',
      api_version: 'API版本',
      min_apiversion: '最低支持API版本',
      os: '操作系统',
      arch: '架构',
      kernel_version: '内核版本',
      build_time: '构建时间',
      git_commit: 'Git提交版本',
    },
    Dockore: {
      hostname: '主机名',
      py_version: 'Python版本',
      saika_version: 'Saika版本',
    },
    Docker: {
      go_version: 'Go版本',
    },
    Engine: {
      experimental: '实验特性',
    }
  },
  container: {
    status: {
      created: '已创建',
      running: '运行中',
      exited: '已退出',
    }
  },
  network: {
    driver: {
      null: '（无）',
      host: '主机',
      bridge: '网桥',
      ipvlan: 'IP VLAN',
      macvlan: 'MAC VLAN',
      overlay: 'Overlay',
    },
    port_protocol: {
      tcp: 'TCP',
      udp: 'UDP',
      sctp: 'SCTP',
    },
  },
  volume: {
    driver: {
      local: '本地设备',
    },
    mount_mode: {
      ro: '只读',
      rw: '读写',
    },
    mount_type: {
      bind: '文件映射',
      volume: '存储卷',
    },
  },
  user: {
    roles: {
      0: '管理员',
      1: '普通用户',
    },
    own_item_type: {
      1: '镜像',
      2: '容器',
      3: '网络',
      4: '存储卷',
    },
  },
  $get(s, i, k) {
    let text_ = this[s][i];
    let text_def = this[s]['_'];

    if (text_ === undefined)
      return k ? text_def[k] ? text_def[k] : k : i;

    if (k === undefined) {
      k = 'this';
      if (text_[k] === undefined)
        return i;
    }

    return text_[k] || (text_def && text_def[k]) || k;
  },
}
