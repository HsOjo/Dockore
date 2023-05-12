<template>
  <el-dialog :visible.sync="dialog_visible" title="指定：Dockore服务器" width="640px">
    <el-form ref="form" :model="form" label-width="120px" style="padding-right: 32px">
      <el-form-item label="服务器地址">
        <el-input placeholder="[域名/IP][:端口]" v-model="form.host" @input="hostInput">
          <template slot="prepend">{{ form.ssl ? 'https' : 'http' }}://</template>
          <template slot="append">
            <el-button @click="sync_host=!sync_host">
              <el-icon :class="`${sync_host?'el-icon-open':'el-icon-turn-off'}`"></el-icon>
            </el-button>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-input placeholder="[域名/IP][:端口]" v-model="form.host_ws" :disabled="sync_host">
          <template slot="prepend">{{ form.ssl ? 'wss' : 'ws' }}://</template>
        </el-input>
      </el-form-item>
    </el-form>

    <span slot="footer" class="dialog-footer">
      <el-button type="info" style="float: left" @click="resetServer">初始化</el-button>
      <el-switch v-model="form.ssl" style="margin-right: 16px" active-text="SSL" inactive-text="不加密"></el-switch>
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="setServer">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
import {mapGetters} from "vuex";

export default {
  name: "SetServerDialog",
  data() {
    return {
      dialog_visible: false,
      form: {},
      sync_host: true,
    }
  },
  computed: {
    ...mapGetters(['serverInfo']),
  },
  methods: {
    hostInput(input) {
      if (this.sync_host)
        this.form.host_ws = input;
    },
    open() {
      this.dialog_visible = true;
      this.form = this.serverInfo || {ssl: true, host: '', host_ws: ''};
      this.sync_host = this.form.host === this.form.host_ws;
    },
    setServer() {
      this.$store.commit('setServerInfo', this.form);
      this.$api.$action.generateURL();
      this.showServer();
      this.dialog_visible = false;
    },
    resetServer() {
      this.$store.commit('setServerInfo', null)
      this.$api.$action.generateURL();
      this.showServer();
      this.dialog_visible = false;
    },
    showServer() {
      this.$helper.sendNotification(
          '指定服务器', `当前服务器为：\n${this.$api.$action.getBaseURL()}\n${this.$api.$action.getWSURL()}`,
          'success', true
      );
    }
  },
  watch: {
    sync_host(nv, ov) {
      if (nv)
        this.form.host_ws = this.form.host;
    }
  }
}
</script>

<style scoped>

</style>
