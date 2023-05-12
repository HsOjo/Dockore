<template>
  <el-dialog :visible.sync="dialog_visible" title="创建网络" :width="collapse? '1024px':'1124px'">
    <el-container>
      <el-aside style="width: auto">
        <el-menu default-active="1" style="text-align: center" @select="x => step = x"
                 ref="menu" :collapse="collapse" class="collapse-menu">
          <el-menu-item index="1">
            <el-icon class="el-icon-connection"></el-icon>
            <span slot="title">网络信息</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon class="el-icon-set-up"></el-icon>
            <span slot="title">高级选项</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <div v-show="step === '1'">
          <div style="width: 480px">
            <el-form ref="form" :model="form" label-width="120px">
              <el-form-item label="网络名称">
                <el-input v-model="form.name"></el-input>
              </el-form-item>
              <el-form-item label="驱动类型">
                <el-select v-model="form.driver" style="width: 100%">
                  <el-option v-for="(k, v) in driverChoices" :key="k" :label="k" :value="v"></el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="子网网段">
                <el-input v-model="form.subnet" placeholder="x.x.x.x/yy"></el-input>
              </el-form-item>
              <el-form-item label="网关">
                <el-input v-model="form.gateway" placeholder="x.x.x.x"></el-input>
              </el-form-item>
              <el-form-item label="IP范围">
                <el-input v-model="form.ip_range" placeholder="x.x.x.x/yy"></el-input>
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="form.attachable">开放连接</el-checkbox>
              </el-form-item>
            </el-form>
          </div>
        </div>
        <div v-show="step === '2'" style="text-align: left">
          <el-table :data="form.options" border>
            <el-table-column label="键" width="320">
              <template slot-scope="scope">
                <el-autocomplete v-model="scope.row.key" style="width: 100%" placeholder="com.docker.network.xxx"
                                 :fetch-suggestions="optionSuggestion"></el-autocomplete>
              </template>
            </el-table-column>
            <el-table-column label="值" width="320">
              <template slot-scope="scope">
                <el-input v-model="scope.row.value" style="width: 100%"></el-input>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template slot-scope="scope">
                <el-button size="nano" type="danger" @click="removeOption(scope.row)">
                  <el-icon class="el-icon-delete"></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 8px">
            <el-button @click="appendOption">
              <el-icon class="el-icon-circle-plus"></el-icon>
            </el-button>
          </div>
        </div>
      </el-main>
    </el-container>
    <span slot="footer" class="dialog-footer">
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="createNetwork" :disabled="!form.name">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
import {ResizeObserver} from "@juggle/resize-observer";

export default {
  name: "CreateDialog",
  data() {
    return {
      dialog_visible: false,
      form: {options: []},
      option_suggestion: [
        'com.docker.network.bridge.name',
        'com.docker.network.bridge.host_binding_ipv4',
        'com.docker.network.bridge.mtu',
        'com.docker.network.bridge.default_bridge',
        'com.docker.network.bridge.enable_icc',
        'com.docker.network.bridge.enable_ip_masquerade',
      ],
      collapse: false,
      ro: null,
      step: '1',
    };
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
  },
  computed: {
    driverChoices() {
      return this.$text.network.driver;
    },
  },
  methods: {
    open() {
      this.dialog_visible = true;
      this.form = {options: [], driver: 'bridge'};
      this.step = '1';
    },

    createNetwork() {
      this.form.options = this.form.options.filter(opt => {
        return opt.key && opt.value;
      });

      this.$api.networkCreate(this.form.name, this.form.driver, this.form.options,
          this.form.attachable, this.form.subnet, this.form.gateway, this.form.ip_range).then(
          resp => {
            if (resp.code === 0)
              this.dialog_visible = false;
            this.$bus.$emit(this.$event.refresh_networks);
          }
      );
    },

    appendOption() {
      this.form.options.push({key: '', value: ''});
    },
    removeOption(item) {
      this.form.options = this.form.options.filter(x => x !== item);
    },

    optionSuggestion(input, cb) {
      let suggestion = [];
      for (let option of this.option_suggestion) {
        if (option.indexOf(input) !== -1)
          suggestion.push({value: option});
      }
      cb(suggestion);
    },

    fit() {
      this.collapse = document.body.clientWidth < 1280;
    },
  },
  watch: {
    step(nv, ov) {
      this.$refs.menu.activeIndex = nv;
    },
  },
}
</script>

<style scoped>
.collapse-menu:not(.el-menu--collapse) {
  width: 224px;
}
</style>
