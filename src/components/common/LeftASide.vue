<template>
  <div style="text-align: center">
    <el-menu ref="menu" v-model="menu_index" :default-active="menu_index"
             :router="true" :collapse="collapse" class="collapse-menu">
      <el-menu-item v-for="item in menu_items" :key="item.path" :index="item.path"
                    v-if="!item.admin||$store.getters.isAdmin">
        <i :class="item.icon"></i>
        <span slot="title">{{ item.title }}</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script>
import {ResizeObserver} from "@juggle/resize-observer";

export default {
  name: "LeftASide",
  data() {
    return {
      menu_index: null,
      menu_items: [
        {path: '/admin/system/config', title: '系统设置', icon: 'el-icon-setting', admin: true},
        {path: '/system/version', title: '系统版本', icon: 'el-icon-warning-outline'},
        {path: '/admin/user', title: '用户管理', icon: 'el-icon-user', admin: true},
        {path: '/image', title: '镜像管理', icon: 'el-icon-document-copy'},
        {path: '/container', title: '容器管理', icon: 'el-icon-copy-document'},
        {path: '/network', title: '网络管理', icon: 'el-icon-connection'},
        {path: '/volume', title: '存储卷管理', icon: 'el-icon-files'},
      ],
      collapse: false,
      ro: null,
    }
  },
  created() {
    this.updateActiveMenu();
    this.$bus.$on(this.$event.update_active_menu, this.updateActiveMenu);
  },
  mounted() {
    this.ro = new ResizeObserver((entries, observer) => {
      this.fit();
    });
    this.ro.observe(document.body);
    this.fit();
  },
  beforeDestroy() {
    this.ro.disconnect();
    this.$bus.$off(this.$event.update_active_menu);
  },
  methods: {
    fit() {
      this.collapse = document.body.clientWidth < 1280;
    },
    updateActiveMenu(path) {
      if (path === undefined)
        path = this.$route.path
      this.menu_index = '';
      for (let item of this.menu_items) {
        if (path.indexOf(item.path) === 0) {
          this.menu_index = item.path;
        }
      }
    }
  }
}
</script>

<style scoped>
.collapse-menu:not(.el-menu--collapse) {
  width: 256px;
}

.el-menu-item.is-active {
  background: #ecf5ff;
}
</style>
