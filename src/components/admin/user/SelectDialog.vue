<template>
  <el-dialog :visible.sync="dialog_visible" :title="title" width="960px">
    <div id="navbar" style="height: 56px">
      <div style="float: left">
        搜索：
        <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px"></el-input>
      </div>
    </div>
    <el-table :data="tableData" border highlight-current-row
              @current-change="tableCurrentChange">
      <el-table-column
          label="用户ID"
          prop="id"
          width="120">
      </el-table-column>
      <el-table-column
          label="用户名"
          prop="username"
          width="200">
      </el-table-column>
      <el-table-column
          label="用户角色"
          prop="role_type"
          width="160">
      </el-table-column>
      <el-table-column
          label="创建时间"
          prop="create_time"
          width="200">
      </el-table-column>
      <el-table-column
          label="使用资源数量"
          prop="owner_item_num"
          width="160">
      </el-table-column>
    </el-table>
    <div style="margin-top: 8px">
      <el-pagination
          :current-page.sync="page" :page-size.sync="per_page"
          :page-sizes="[5, 10, 50, 100]" :total="total" @size-change="getUserItems"
          background layout="prev, pager, next, sizes"></el-pagination>
    </div>
    <span slot="footer" class="dialog-footer">
      <el-button @click="close">取 消</el-button>
      <el-button type="primary" @click="confirm" :disabled="!item">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: "SelectDialog",
  data() {
    return {
      dialog_visible: false,
      total: 0,
      page: 1,
      per_page: 10,
      items: [],
      keyword: '',
      callback: null,
      item: null,
      title: '',
      filter: null,
    };
  },
  computed: {
    tableData() {
      let items = this.$helper.copyObject(this.items);
      if (this.filter)
        items = items.filter(this.filter);

      for (let item of items) {
        item.role_type = this.$text.$get('user', 'roles', item.role_type);
        item.create_time = this.$moment(item.create_time).from();
      }
      return items;
    },
  },
  methods: {
    open(callback, title, filter) {
      this.dialog_visible = true;
      this.title = title ? title : '选择用户';
      this.filter = filter ? filter : null;
      this.callback = callback;
      this.item = null;
      this.getUserItems();
    },
    close() {
      this.dialog_visible = false;
    },
    tableCurrentChange(n, o) {
      this.item = n;
    },
    confirm() {
      this.callback(this.item.id);
    },
    getUserItems() {
      this.$api.adminUserList(this.page, this.per_page, this.keyword).then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      );
    },
  },
}
</script>

<style scoped>

</style>
