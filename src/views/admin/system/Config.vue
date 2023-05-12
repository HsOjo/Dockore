<template>
  <div>
    <el-tabs v-model="tab">
      <el-tab-pane :label="text(i)" v-for="(s, i) in form" :key="i">
        <el-form :model="s" label-width="160px">
          <el-form-item v-if="typeof s[k] !== 'object'" :label="text(i, k)" v-for="(v, k) in s" :key="k">
            <template v-if="typeof s[k] === 'string'">
              <el-input v-model="s[k]" type="password" v-if="k.indexOf('password') !== -1"></el-input>
              <el-input v-model="s[k]" v-else></el-input>
            </template>
            <el-input-number v-model="s[k]" type="" v-else-if="typeof s[k] === 'number'"></el-input-number>
            <el-switch v-model="s[k]" type="" v-else-if="typeof s[k] === 'boolean'"></el-switch>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="updateConfig">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
export default {
  name: "Config",
  data() {
    return {
      tab: '',
      form: {},
    }
  },
  created() {
    this.getConfig();
  },
  methods: {
    getConfig() {
      this.$api.adminQueryConfig().then(
          resp => {
            this.form = resp.data.config;
          }
      );
    },
    updateConfig() {
      this.$api.adminUpdateConfig(this.form).then(
          resp => this.getConfig()
      );
    },
    text(i, k) {
      return this.$text.$get('config', i, k);
    },
  },
}
</script>

<style scoped>
.el-form {
  width: 640px;
}

.el-tab-pane {
  padding-top: 16px;
  padding-left: 16px;
}

.el-tabs {
  padding-left: 16px;
}
</style>
