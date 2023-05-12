<template>
  <el-dialog :visible.sync="dialog_visible" title="连接容器网络" :width="collapse? '880px':'1024px'">
    <el-container>
      <el-aside style="width: auto">
        <el-menu ref="menu" default-active="1" @select="x => step = x"
                 style="text-align: center" :collapse="collapse" class="collapse-menu">
          <el-menu-item index="1">
            <el-icon class="el-icon-document-copy"></el-icon>
            <span slot="title">选择容器</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon class="el-icon-copy-document"></el-icon>
            <span slot="title">网络信息</span>
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
                label="ID"
                prop="id"
                width="120">
            </el-table-column>
            <el-table-column
                label="名称"
                prop="name"
                width="200">
            </el-table-column>
            <el-table-column
                label="创建时间"
                prop="create_time"
                width="200">
            </el-table-column>
            <el-table-column
                label="状态"
                prop="status"
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
              <el-form-item label="网络ID">
                <el-input v-model="form.id" readonly></el-input>
              </el-form-item>
              <el-form-item label="网络名称">
                <el-input v-model="item.name" readonly></el-input>
              </el-form-item>
              <el-form-item label="容器ID">
                <el-input v-model="form.container_id" readonly></el-input>
              </el-form-item>
              <el-form-item label="容器名称">
                <el-input v-model="container.name" readonly></el-input>
              </el-form-item>
              <el-form-item label="分配IPv4地址">
                <el-input v-model="form.ipv4_address"
                          :placeholder="`（子网：${item.subnet} 范围：${item.ip_range}）`"></el-input>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-main>
    </el-container>
    <span slot="footer" class="dialog-footer">
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="connectNetwork" :disabled="!form.container_id">确 定</el-button>
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
      container: {},
      item: {containers: []},
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
    tableData() {
      let items = this.items;
      let existed_ids = this.item.containers.map(item => item.id);
      items = items.filter(item => existed_ids.indexOf(item.id) === -1);

      if (this.keyword) {
        items = items.filter(item => item.name.indexOf(this.keyword) !== -1 || item.id.indexOf(this.keyword) !== -1);
      }
      items = items.slice(
          (this.page - 1) * this.page_size,
          this.page * this.page_size
      );

      items = this.$helper.copyObject(items);
      for (let item of items) {
        item.status = this.$text.$get('container', 'status', item.status);
        item.create_time = this.$moment(item.create_time).from();
      }
      return items;
    },
  },
  methods: {
    open(id) {
      this.dialog_visible = true;
      this.step = '1';
      this.form = {id, container_id: '', ipv4_address: ''};
      this.loadNetworkInfo(id)
      this.getContainerItems();
    },
    tableCurrentChange(n, o) {
      if (n) {
        this.loadContainerInfo(n.id, () => {
          this.step = '2';
        });
      }
    },

    getContainerItems() {
      this.$api.containerList(true).then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      )
    },

    loadNetworkInfo(id) {
      this.$api.networkItem(id).then(
          resp => {
            if (resp.code === 0) {
              this.item = resp.data.item;
              this.form.id = this.item.id;
            }
          }
      )
    },

    loadContainerInfo(id, callback) {
      this.$api.containerItem(id).then(
          resp => {
            if (resp.code === 0) {
              this.container = resp.data.item;
              this.form.container_id = this.container.id;
              callback();
            }
          }
      )
    },

    connectNetwork() {
      this.$api.networkConnect(this.form.id, this.form.container_id, this.form.ipv4_address).then(
          resp => {
            if (resp.code === 0)
              this.dialog_visible = false;
          }
      )
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
