<template>
  <div>
    <div style="height: 56px">
      <div style="float: left">
        搜索：
        <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px" @keyup.enter.native="getUserItems">
          <el-button slot="append" icon="el-icon-search" @click="getUserItems"></el-button>
        </el-input>
      </div>
      <div style="float: right">
        <el-button-group style="margin-right: 16px">
          <el-button v-if="selection.length" type="danger" @click="deleteUserItems(selectionIds)">
            <el-icon class="el-icon-delete"></el-icon>
            删除
          </el-button>
        </el-button-group>
        <el-button circle @click="getUserItems">
          <el-icon class="el-icon-refresh"></el-icon>
        </el-button>
        <el-button @click="addUserItem">添加用户</el-button>
      </div>
    </div>
    <el-table :data="tableData" border @selection-change="handleSelectionChange">
      <el-table-column
          type="selection"
          width="55">
      </el-table-column>
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
      <el-table-column
          fixed="right"
          label="操作"
          width="160">
        <template slot-scope="scope">
          <el-button size="mini" @click="editUserItem(scope.row.id)">编辑</el-button>
          <el-button size="mini" type="danger" @click="deleteUserItems([scope.row.id])">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 8px">
      <el-pagination
          :current-page.sync="page" :page-size.sync="per_page"
          :page-sizes="[5, 10, 50, 100]" :total="total" @size-change="getUserItems"
          background layout="prev, pager, next, sizes"></el-pagination>
    </div>
  </div>
</template>

<script>
export default {
  name: "Index",
  computed: {
    tableData() {
      let items = this.$helper.copyObject(this.items);
      for (let item of items) {
        item.role_type = this.$text.$get('user', 'roles', item.role_type);
        item.create_time = this.$moment(item.create_time).from();
      }
      return items;
    },
    selectionIds() {
      return this.selection.map(items => items.id);
    },
  },
  data() {
    return {
      total: 0,
      page: 1,
      per_page: 10,
      items: [],
      keyword: '',
      selection: [],
    }
  },
  created() {
    this.getUserItems();
  },
  methods: {
    handleSelectionChange(val) {
      this.selection = val;
    },
    getUserItems() {
      this.$api.adminUserList(this.page, this.per_page, this.keyword).then(
          resp => {
            this.total = resp.data.total;
            this.page = resp.data.page;
            this.per_page = resp.data.per_page;
            this.items = resp.data.items;
          }
      )
    },
    addUserItem() {
      this.$router.push('/admin/user/add')
    },
    editUserItem(id) {
      this.$router.push(`/admin/user/edit/${id}`)
    },
    deleteUserItems(ids) {
      this.$api.adminUserDelete(ids).then(
          resp => this.getUserItems()
      );
    },
  },
}
</script>

<style scoped>

</style>
