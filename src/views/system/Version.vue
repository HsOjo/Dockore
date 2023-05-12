<template>
  <div>
    <el-tabs v-model="tab">
      <el-tab-pane :label="text(i)" v-for="(s, i) in version" :key="i">
        <el-form :model="s" label-width="160px">
          <el-form-item :label="text(i, k)" v-for="(v, k) in s" :key="k">
            <template v-if="typeof s[k] === 'string'">
              <el-date-picker v-model="s[k]" v-if="k.indexOf('_time') !== -1" type="datetime" readonly></el-date-picker>
              <el-switch v-model="s[k]" v-else-if="['true', 'false'].indexOf(s[k].toLowerCase()) !== -1"
                         disabled></el-switch>
              <el-input v-model="s[k]" v-else readonly></el-input>
            </template>
            <el-input-number v-model="s[k]" v-else-if="typeof s[k] === 'number'" readonly></el-input-number>
            <el-switch v-model="s[k]" v-else-if="typeof s[k] === 'boolean'" disabled></el-switch>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
export default {
  name: "Version",
  data() {
    return {
      tab: '',
      version: [],
    }
  },
  created() {
    if (this.$store.getters.userToken)
      this.getVersion();
  },
  methods: {
    getVersion() {
      this.$api.queryVersion().then(
          resp => {
            if (resp.code === 0)
              this.version = resp.data.version;
          }
      )
    },
    text(i, k) {
      return this.$text.$get('version', i, k);
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
