<template>
  <div>
    <div style="display: flex; align-items: center; margin: 8px 8px 16px;">
      <el-breadcrumb separator-class="el-icon-arrow-right">
        <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
        <el-breadcrumb-item to="/network">网络管理</el-breadcrumb-item>
        <el-breadcrumb-item :to="`/network/${item.id}`">
          网络：{{ item.id }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="基本信息" name="basic">
        <el-form :model="item" label-width="120px">
          <el-form-item label="ID">
            <el-input v-model="item.id" readonly></el-input>
          </el-form-item>
          <el-form-item label="名称">
            <el-input v-model="item.name" readonly></el-input>
          </el-form-item>
          <el-form-item label="驱动类型">
            <el-input v-model="itemDriver" readonly></el-input>
          </el-form-item>
          <el-form-item label="范围">
            <el-input v-model="item.scope" readonly></el-input>
          </el-form-item>
          <el-form-item label="创建时间">
            <el-input v-model="itemCreateTime" readonly></el-input>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="网络信息" name="options">
        <el-card shadow="hover" style="width: 720px">
          <div slot="header">
            <span>高级选项</span>
          </div>
          <el-table :data="itemOptions" border>
            <el-table-column label="键" prop="key" width="400"></el-table-column>
            <el-table-column label="值" prop="value" width="240"></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="容器列表" name="containers">
        <el-table :data="tableData" border @selection-change="handleSelectionChange">
          <el-table-column
              type="selection"
              width="55">
          </el-table-column>
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
              label="IP"
              prop="ip"
              width="160">
          </el-table-column>
          <el-table-column
              label="前缀"
              prop="prefix"
              width="120">
          </el-table-column>
          <el-table-column
              label="网关"
              prop="gateway"
              width="160">
          </el-table-column>
          <el-table-column
              fixed="right"
              label="操作"
              width="240">
            <template slot-scope="scope">
              <router-link :to="`/container/${scope.row.id}`" class="el-button el-button--mini">信息</router-link>
              <el-button size="mini" type="danger" @click="disconnectContainerItem(scope.row.id)">断开网络</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="float: right; margin: 16px">
          <el-checkbox v-model="force" label="强制断开" style="margin-right: 8px"></el-checkbox>
          <el-button v-if="selection.length" type="danger" @click="disconnectContainerItems(selectionIds)">
            断开选中
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
export default {
  name: "Item",
  computed: {
    selectionIds() {
      return this.selection.map(items => items.id);
    },
    itemCreateTime() {
      if (this.item.create_time)
        return this.$moment(this.item.create_time).from();
    },
    itemDriver() {
      if (this.item.driver)
        return this.$text.$get('network', 'driver', this.item.driver);
    },
    itemOptions() {
      let result = [];
      let options = this.item.options;
      if (options)
        for (let key in options)
          result.push({key: key, value: options[key]})
      return result;
    },
    tableData() {
      let items = this.item.containers;
      items = this.$helper.copyObject(items);
      for (let item of items) {
        item.ip = item.network.ip;
        item.prefix = item.network.prefix;
        item.gateway = item.network.gateway;
      }
      return items;
    },
  },
  data() {
    return {
      tab: 'basic',
      item: {containers: []},
      selection: [],
      force: false,
    }
  },
  created() {
    this.getItemInfo(this.$route.params.id);
  },
  methods: {
    handleSelectionChange(val) {
      this.selection = val;
    },
    getItemInfo(id) {
      this.$api.networkItem(id).then(
          resp => {
            if (resp.code === 0)
              this.item = resp.data.item;
          }
      )
    },
    deleteNetworkItems(ids) {
      this.$api.networkDelete(ids).then(
          resp => {
            this.getItemInfo(this.item.id);
          }
      );
    },
    disconnectContainerItem(id, reload) {
      if (reload === undefined)
        reload = true;
      this.$api.networkDisconnect(this.item.id, id, this.force).then(
          resp => {
            if (reload)
              this.getItemInfo(this.item.id)
          }
      )
    },
    disconnectContainerItems(ids) {
      let i = 0;
      ids.map(id => {
        setTimeout(() => this.disconnectContainerItem(id, i + 1 >= ids.length), i++ * 300);
      });
    }
  }
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
