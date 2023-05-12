<template>
  <div>
    <div style="margin: 0 8px 16px; display: flex; justify-content: space-between">
      <div style="display: flex; align-items: center">
        <el-breadcrumb separator-class="el-icon-arrow-right">
          <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
          <el-breadcrumb-item to="/container">容器管理</el-breadcrumb-item>
          <el-breadcrumb-item :to="`/container/${item.id}`">
            <template v-if="item.name">终端：{{ item.name }}</template>
            <template v-else>容器终端</template>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div>
        <el-button-group style="margin-right: 16px" v-if="this.item.id">
          <el-button type="danger" @click="stopContainer">
            <el-icon class="el-icon-video-pause"></el-icon>
            停止
          </el-button>
          <el-button type="warning" @click="restartContainer">
            <el-icon class="el-icon-refresh-right"></el-icon>
            重启
          </el-button>
          <el-button type="success" @click="startContainer">
            <el-icon class="el-icon-video-play"></el-icon>
            启动
          </el-button>
        </el-button-group>
        <el-button circle @click="refresh">
          <el-icon class="el-icon-refresh"></el-icon>
        </el-button>
      </div>
    </div>
    <el-card shadow="hover">
      <div ref="terminal" style="width: 100%; height: calc(100vh - 224px);"></div>
    </el-card>
  </div>
</template>

<script>
import "~xterm/css/xterm.css"
import {Terminal} from 'xterm';
import {WebLinksAddon} from 'xterm-addon-web-links'
import {FitAddon} from 'xterm-addon-fit'
import {SearchAddon} from 'xterm-addon-search'
import {ResizeObserver} from '@juggle/resize-observer';
import helper from "@/utils/helper";

export default {
  name: "Terminal",
  computed: {
    token() {
      return this.$route.params.token;
    }
  },
  data() {
    return {
      term: new Terminal({
        cursorBlink: true,
        macOptionIsMeta: true,
      }),
      web_link: new WebLinksAddon(),
      fit: new FitAddon(),
      search: new SearchAddon(),
      ro: null,
      item: {},
    };
  },
  created() {
    this.$connect(`${this.$api.$action.getWSURL()}/socket/container/terminal`);
    this.term.loadAddon(this.web_link);
    this.term.loadAddon(this.fit);
    this.term.loadAddon(this.search);
  },
  mounted() {
    this.term.open(this.$refs.terminal);
    this.term.onData(this.pty_input);
    this.fit.fit();
  },
  sockets: {
    onopen() {
      this.ro = new ResizeObserver((entries, observer) => {
        this.fitToscreen();
      });
      this.ro.observe(this.$refs.terminal);

      this.emit('open', {
        user_token: this.$store.getters.userToken,
        token: this.token,
      });
    },
    onclose() {
      helper.sendNotification('容器终端', '网络连接中断。', 'warning');
      this.term.write(
          '\r\n' +
          ' --==========================--\r\n' +
          '  * Terminal: Network was down.\r\n' +
          ' --==========================--\r\n'
      )
    },
    onmessage(event) {
      let msg = JSON.parse(event.data);
      let callback = this[msg.event];
      if (callback)
        callback(msg.data);
    },
  },
  methods: {
    emit(event, data) {
      return this.$socket.send(JSON.stringify({
        event, data
      }));
    },
    init_success(item) {
      this.item = item;
      helper.sendNotification('容器终端', '打开容器终端成功。', 'success');
      this.fitToscreen();
    },
    init_failed(resp) {
      helper.sendNotification('容器终端', resp.msg ? resp.msg : '打开容器终端失败。', 'error');
    },
    pty_input(key, domEvent) {
      this.emit("pty_input", {input: key});
    },
    pty_output(data) {
      this.term.write(data.output)
    },
    fitToscreen() {
      this.$helper.debounce(() => {
        this.fit.fit();
        this.emit("resize", {"cols": this.term.cols, "rows": this.term.rows});
      }, 1000)
    },
    startContainer() {
      this.$api.containerStart([this.item.id]).then(this.refresh);
    },
    stopContainer() {
      this.$api.containerStop([this.item.id], 5);
    },
    restartContainer() {
      this.$api.containerRestart([this.item.id], 5).then(this.refresh);
    },
    refresh() {
      this.$router.go(0);
    },
  },
  beforeDestroy() {
    this.ro.disconnect();
    this.$disconnect();
  },
}
</script>

<style scoped>

</style>
