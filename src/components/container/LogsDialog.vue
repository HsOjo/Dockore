<template>
  <el-dialog :visible.sync="dialog_visible" title="容器操作日志" width="1280px">
    操作时间段：
    <el-date-picker
        v-model="dt_range"
        end-placeholder="结束日期"
        range-separator="至"
        start-placeholder="开始日期"
        type="datetimerange">
    </el-date-picker>
    <el-button circle style="margin-left: 8px" @click="catchContainerLogs">
      <el-icon class="el-icon-takeaway-box"></el-icon>
    </el-button>
    <!--    <el-input v-model="logs" :autosize="{ minRows: 10, maxRows: 20 }"-->
    <!--              readonly style="margin-top: 8px" type="textarea"></el-input>-->
    <div ref="terminal" class="terminal"></div>
  </el-dialog>
</template>

<script>
import "~xterm/css/xterm.css"
import {Terminal} from 'xterm';
import {WebLinksAddon} from 'xterm-addon-web-links'
import {FitAddon} from 'xterm-addon-fit'
import {SearchAddon} from 'xterm-addon-search'

export default {
  name: "LogsDialog",
  data() {
    return {
      dialog_visible: false,
      dt_range: [],
      id: '',
      logs: '',

      init: false,
      term: new Terminal({
        cursorBlink: true,
        macOptionIsMeta: true,
      }),
      web_link: new WebLinksAddon(),
      fit: new FitAddon(),
      search: new SearchAddon(),
    }
  },
  created() {
    this.term.loadAddon(this.web_link);
    this.term.loadAddon(this.fit);
    this.term.loadAddon(this.search);
  },
  methods: {
    open(id) {
      this.id = id;
      this.logs = '';
      this.dt_range = [];
      this.dialog_visible = true;
      if (this.init)
        this.term.clear();
    },
    openTerminal() {
      if (this.init)
        return

      this.term.open(this.$refs.terminal);
      this.fit.fit();
      this.init = true;
    },
    catchContainerLogs() {
      this.openTerminal();

      let since, until;
      if (this.dt_range.length >= 2) {
        this.dt_range = this.dt_range.map(
            x => this.$moment(x).format('YYYY-MM-DD HH:mm:ss')
        );
        [since, until] = this.dt_range;
      }
      this.$api.containerLogs(this.id, since, until).then(
          resp => {
            if (resp.code === 0)
              this.logs = resp.data.content;
          }
      );
    }
  },
  watch: {
    logs(nv, ov) {
      this.term.write(nv);
    },
  },
}
</script>

<style scoped>

.terminal {
  margin-top: 16px;
  width: 100%;
  height: 360px;
  background: black;
}
</style>
