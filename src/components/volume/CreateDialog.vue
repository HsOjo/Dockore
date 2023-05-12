<template>
  <el-dialog :visible.sync="dialog_visible" title="创建存储卷" :width="collapse? '1024px':'1124px'">
    <el-container>
      <el-aside style="width: auto">
        <el-menu default-active="1" style="text-align: center" @select="x => step = x"
                 ref="menu" :collapse="collapse" class="collapse-menu">
          <el-menu-item index="1">
            <el-icon class="el-icon-files"></el-icon>
            <span slot="title">存储卷信息</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon class="el-icon-odometer"></el-icon>
            <span slot="title">驱动器选项</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <div v-show="step === '1'">
          <div style="width: 480px">
            <el-form ref="form" :model="form" label-width="120px">
              <el-form-item label="存储卷名称">
                <el-input v-model="form.name"></el-input>
              </el-form-item>
              <el-form-item label="驱动器类型">
                <el-select v-model="form.driver" style="width: 100%">
                  <el-option v-for="(k, v) in driverChoices" :key="k" :label="k" :value="v"></el-option>
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </div>
        <div v-show="step === '2'" style="text-align: left">
          <el-table :data="form.driver_opts" border>
            <el-table-column label="键" width="320">
              <template slot-scope="scope">
                <el-autocomplete v-model="scope.row.key" style="width: 100%"
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
                <el-button size="nano" type="danger" @click="removeDriverOption(scope.row)">
                  <el-icon class="el-icon-delete"></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 8px">
            <el-button @click="appendDriverOption">
              <el-icon class="el-icon-circle-plus"></el-icon>
            </el-button>
          </div>
        </div>
      </el-main>
    </el-container>
    <span slot="footer" class="dialog-footer">
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="createVolume" :disabled="!form.name">确 定</el-button>
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
      form: {driver_opts: []},
      driver_option_suggestion: ['type', 'device', 'o'],
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
      return this.$text.volume.driver;
    },
  },
  methods: {
    open() {
      this.dialog_visible = true;
      this.form = {driver_opts: [], driver: 'local'};
      this.step = '1';
    },

    createVolume() {
      this.form.driver_opts = this.form.driver_opts.filter(opt => {
        return opt.key && opt.value;
      });

      this.$api.volumeCreate(this.form.name, this.form.driver, this.form.driver_opts).then(
          resp => {
            if (resp.code === 0)
              this.dialog_visible = false;
            this.$bus.$emit(this.$event.refresh_volumes);
          }
      );
    },

    appendDriverOption() {
      this.form.driver_opts.push({key: '', value: ''});
    },
    removeDriverOption(item) {
      this.form.driver_opts = this.form.driver_opts.filter(x => x !== item);
    },

    optionSuggestion(input, cb) {
      let suggestion = [];
      for (let option of this.driver_option_suggestion) {
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
