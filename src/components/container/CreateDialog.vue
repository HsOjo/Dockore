<template>
  <el-dialog :visible.sync="dialog_visible" title="创建容器" :width="collapse? '1124px':'1280px'">
    <el-container>
      <el-aside style="width: auto">
        <el-menu ref="menu" default-active="1" @select="x => step = x"
                 style="text-align: center" :collapse="collapse" class="collapse-menu">
          <el-menu-item index="1">
            <el-icon class="el-icon-document-copy"></el-icon>
            <span slot="title">选择镜像</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon class="el-icon-copy-document"></el-icon>
            <span slot="title">容器信息</span>
          </el-menu-item>
          <el-menu-item index="3">
            <el-icon class="el-icon-link"></el-icon>
            <span slot="title">端口映射</span>
          </el-menu-item>
          <el-menu-item index="4">
            <el-icon class="el-icon-files"></el-icon>
            <span slot="title">存储挂载</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <div v-show="step === '1'">
          <div id="navbar" style="height: 56px">
            <div style="float: left">
              搜索：
              <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px"></el-input>
            </div>
          </div>
          <el-table ref="table" :data="tableData" border highlight-current-row
                    @current-change="tableCurrentChange">
            <el-table-column
                label="镜像ID"
                prop="id"
                width="160">
            </el-table-column>
            <el-table-column
                label="标签"
                width="240">
              <template slot-scope="scope">
                <el-tag v-for="tag in scope.row.tags" :key="tag" type="info">{{ tag }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column
                label="镜像作者"
                prop="author"
                width="220">
            </el-table-column>
            <el-table-column
                label="创建时间"
                prop="create_time"
                width="200">
            </el-table-column>
            <el-table-column
                label="镜像尺寸"
                prop="size"
                width="120">
            </el-table-column>
          </el-table>
          <div style="margin-top: 8px">
            <el-pagination
                :current-page.sync="page" :page-size.sync="page_size"
                :page-sizes="[5, 10, 50, 100]" :total="this.items.length"
                background layout="prev, pager, next, sizes"></el-pagination>
          </div>
        </div>
        <div v-show="step === '2'">
          <div style="width: 480px">
            <el-form ref="form" :model="form" label-width="120px">
              <el-form-item label="容器名称">
                <el-input v-model="form.name"></el-input>
              </el-form-item>
              <el-form-item label="镜像名称">
                <el-input v-model="form.image" readonly></el-input>
              </el-form-item>
              <el-form-item label="镜像标签">
                <el-select v-model="form.tag" placeholder="tag" style="width: 100%">
                  <el-option v-for="tag in selectionTags" :key="tag" :label="tag" :value="tag"></el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="启动命令">
                <el-input v-model="form.command"></el-input>
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="form.tty">虚拟终端</el-checkbox>
                <el-checkbox v-model="form.interactive">交互模式</el-checkbox>
              </el-form-item>
            </el-form>
          </div>
        </div>
        <div v-show="step === '3'">
          <el-table :data="form.ports" border>
            <el-table-column label="内部端口" width="160">
              <template slot-scope="scope">
                <el-autocomplete v-model="scope.row.port" :fetch-suggestions="portSuggestion"></el-autocomplete>
              </template>
            </el-table-column>
            <el-table-column label="协议" width="160">
              <template slot-scope="scope">
                <el-select v-model="scope.row.protocol">
                  <el-option v-for="(k, v) in portProtocols" :key="k" :label="k" :value="v"></el-option>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="监听地址" width="240">
              <template slot-scope="scope">
                <el-autocomplete v-model="scope.row.listen_ip" :fetch-suggestions="ipSuggestion"></el-autocomplete>
              </template>
            </el-table-column>
            <el-table-column label="监听端口" width="160">
              <template slot-scope="scope">
                <el-autocomplete v-model="scope.row.listen_port" :fetch-suggestions="portSuggestion"></el-autocomplete>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template slot-scope="scope">
                <el-button size="nano" type="danger" @click="removePortMapping(scope.row)">
                  <el-icon class="el-icon-delete"></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 8px">
            <el-button @click="appendPortMapping">
              <el-icon class="el-icon-circle-plus"></el-icon>
            </el-button>
          </div>
        </div>
        <div v-show="step === '4'">
          <el-table :data="form.volumes" border>
            <el-table-column label="存储卷" width="240">
              <template slot-scope="scope">
                <el-autocomplete v-model="scope.row.path" :fetch-suggestions="pathSuggestion"></el-autocomplete>
              </template>
            </el-table-column>
            <el-table-column label="挂载模式" width="160">
              <template slot-scope="scope">
                <el-select v-model="scope.row.mode">
                  <el-option v-for="(k, v) in mountModes" :key="k" :label="k" :value="v"></el-option>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="挂载位置" width="240">
              <template slot-scope="scope">
                <el-input v-model="scope.row.bind"></el-input>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template slot-scope="scope">
                <el-button size="nano" type="danger" @click="removeVolumeMapping(scope.row)">
                  <el-icon class="el-icon-delete"></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 8px">
            <el-button @click="appendVolumeMapping">
              <el-icon class="el-icon-circle-plus"></el-icon>
            </el-button>
          </div>
        </div>
      </el-main>
    </el-container>
    <span slot="footer" class="dialog-footer">
      <el-switch v-model="run" style="margin-right: 16px"
                 active-text="运行容器" inactive-text="仅创建">
      </el-switch>
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="createContainer" :disabled="!form.image">确 定</el-button>
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
      items: [],
      keyword: '',
      step: '1',
      page: 1,
      page_size: 10,
      form: {},
      item: {tags: []},
      port_suggestion: [22, 53, 80, 443],
      ip_suggestion: ['0.0.0.0', '127.0.0.1'],
      volumes: [],
      run: true,
      collapse: false,
      ro: null,
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
    portProtocols() {
      return this.$text.network.port_protocol;
    },
    mountModes() {
      return this.$text.volume.mount_mode;
    },
    tableData() {
      let items = this.items;
      if (this.keyword) {
        items = items.filter(item => item.tags.join(',').indexOf(this.keyword) !== -1 || item.id.indexOf(this.keyword) !== -1);
      }
      items = items.slice(
          (this.page - 1) * this.page_size,
          this.page * this.page_size
      );

      items = this.$helper.copyObject(items);
      for (let item of items) {
        item.create_time = this.$moment(item.create_time).from();
      }
      return items;
    },
    selectionName() {
      return this.item.tags[0].split(':')[0] || 'latest'
    },
    selectionTags() {
      let a = [];
      for (let tag of this.item.tags) {
        a.push(tag.split(':')[1])
      }
      return a;
    },
  },
  methods: {
    open() {
      this.dialog_visible = true;
      this.step = '1';
      this.form = {name: '', image: '', tag: '', command: '', interactive: false, tty: false, ports: [], volumes: []};
      this.getImageItems();
      this.getVolumeItems();
    },
    tableCurrentChange(n, o) {
      if (n) {
        this.loadImageInfo(n.id, () => {
          this.step = '2';
        });
      }
    },

    getImageItems() {
      this.$api.imageList(false).then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      )
    },

    getVolumeItems() {
      this.$api.volumeList().then(
          resp => {
            if (resp.code === 0)
              this.volumes = resp.data.items;
          }
      )
    },

    loadImageInfo(id, callback) {
      this.$api.imageItem(id).then(
          resp => {
            if (resp.code === 0) {
              this.item = resp.data.item;
              this.form.image = this.selectionName;
              this.form.tag = this.selectionTags[0];
              this.form.command = this.item.command;
              this.form.interactive = this.item.interactive;
              this.form.tty = this.item.tty;
              this.form.ports = this.item.ports.map(({port, protocol}) => {
                return {
                  port: port.toString(), protocol,
                  listen_ip: '0.0.0.0', listen_port: port.toString()
                }
              })
              callback();
            }
          }
      )
    },

    createContainer() {
      this.form.ports = this.form.ports.filter(item => {
        return item.port && item.protocol && item.listen_ip && item.listen_port;
      })
      this.form.volumes = this.form.volumes.filter(item => {
        return item.path && item.mode && item.bind;
      })

      let api = this.$api.containerCreate;
      if (this.run)
        api = this.$api.containerRun;
      api(`${this.form.image}:${this.form.tag}`, this.form.command,
          this.form.name, this.form.interactive, this.form.tty, this.form.ports, this.form.volumes).then(
          resp => {
            if (resp.code === 0)
              this.dialog_visible = false;
            this.$bus.$emit(this.$event.refresh_containers);
          }
      )
    },

    appendVolumeMapping() {
      this.form.volumes.push({path: '', mode: 'rw', bind: ''});
    },
    removeVolumeMapping(item) {
      this.form.volumes = this.form.volumes.filter(x => x !== item);
    },

    pathSuggestion(input, cb) {
      let suggestion = [];
      for (let volume of this.volumes) {
        if (volume.name.indexOf(input) !== -1)
          suggestion.push({value: volume.name});
      }
      cb(suggestion);
    },

    appendPortMapping() {
      this.form.ports.push({protocol: 'tcp', listen_ip: '0.0.0.0'});
    },
    removePortMapping(item) {
      this.form.ports = this.form.ports.filter(x => x !== item);
    },

    portSuggestion(input, cb) {
      let suggestion = [];
      for (let port of this.port_suggestion) {
        let port_str = port.toString();
        if (port_str.indexOf(input) !== -1)
          suggestion.push({value: port_str});
      }
      cb(suggestion);
    },
    ipSuggestion(input, cb) {
      let suggestion = [];
      for (let ip of this.ip_suggestion) {
        if (ip.indexOf(input) !== -1)
          suggestion.push({value: ip});
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
