<template>
  <div>
    <div style="display: flex; align-items: center; margin: 8px 8px 32px;">
      <el-breadcrumb separator-class="el-icon-arrow-right">
        <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
        <el-breadcrumb-item to="/admin/user">用户管理</el-breadcrumb-item>
        <el-breadcrumb-item to="/admin/user/add" v-if="isAdd">添加用户</el-breadcrumb-item>
        <el-breadcrumb-item :to="`/admin/user/edit/${item.id}`" v-else>
          用户：{{ item.username }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <el-tabs v-model="tab">
      <el-tab-pane label="基本信息" name="basic">
        <el-form :model="item" label-width="120px">
          <el-form-item label="用户名">
            <el-input v-model="item.username"></el-input>
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="item.password" type="password" v-if="isAdd"></el-input>
            <el-input v-model="item.password" type="password" v-else placeholder="（留空则不修改密码）"></el-input>
          </el-form-item>
          <el-form-item label="用户角色">
            <el-select v-model="item.role_type" style="width: 100%">
              <el-option v-for="(k, v) in roleChoices" :key="k" :label="k" :value="parseInt(v)"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="addUserItem" v-if="isAdd">添加</el-button>
            <el-button type="primary" @click="editUserItem" v-else>保存</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="权限信息" name="owner" v-if="!isAdd">
        <el-table :data="tableData" border @selection-change="handleSelectionChange">
          <el-table-column
              type="selection"
              width="55">
          </el-table-column>
          <el-table-column
              label="对象类型"
              prop="type_"
              width="160">
          </el-table-column>
          <el-table-column
              label="对象ID"
              prop="obj_id"
              width="200">
          </el-table-column>
          <el-table-column
              label="授权时间"
              prop="create_time"
              width="200">
          </el-table-column>
          <el-table-column
              fixed="right"
              label="操作"
              width="200">
            <template slot-scope="scope">
              <router-link
                  :to="`/image/${scope.row.obj_id}`"
                  class="el-button el-button--mini"
                  v-if="scope.row.type === 1">信息
              </router-link>
              <router-link
                  :to="`/container/${scope.row.obj_id}`"
                  class="el-button el-button--mini"
                  v-else-if="scope.row.type === 2">信息
              </router-link>
              <router-link
                  :to="`/network/${scope.row.obj_id}`"
                  class="el-button el-button--mini"
                  v-else-if="scope.row.type === 3">信息
              </router-link>
              <router-link
                  :to="`/volume/${scope.row.obj_id}`"
                  class="el-button el-button--mini"
                  v-else-if="scope.row.type === 4">信息
              </router-link>
              <el-button size="mini" type="danger" @click="removeOwnerShips([scope.row.id])">移除所有权</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="float: right; margin: 16px">
          <el-button v-if="selection.length" type="danger" @click="removeOwnerShips(selectionIds)">
            <el-icon class="el-icon-delete"></el-icon>
            移除选中
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
    tableData() {
      let items = this.$helper.copyObject(this.item.own_items);
      for (let item of items) {
        item.type_ = this.$text.$get('user', 'own_item_type', item.type);
        item.create_time = this.$moment(item.create_time).from();
      }
      return items;
    },
    id() {
      return this.$route.params.id;
    },
    isAdd() {
      return !this.id;
    },
    roleChoices() {
      return this.$text.user.roles;
    },
  },
  data() {
    return {
      tab: 'basic',
      item: {own_items: []},
      selection: [],
    }
  },
  created() {
    if (!this.isAdd)
      this.getUserItem(this.id);
  },
  methods: {
    handleSelectionChange(val) {
      this.selection = val;
    },
    getUserItem(id) {
      this.$api.adminUserItem(id).then(
          resp => {
            if (resp.code === 0)
              this.item = resp.data.item;
          }
      )
    },
    addUserItem() {
      this.$api.adminUserAdd(this.item.username, this.item.password, this.item.role_type).then(
          resp => {
            if (resp.code === 0)
              this.$router.push('/admin/user');
          }
      )
    },
    editUserItem() {
      this.$api.adminUserEdit(this.item.id, this.item.username, this.item.password, this.item.role_type).then(
          resp => {
            if (resp.code === 0) {
              if (this.item.id === this.$store.getters.userInfo.id) {
                this.$bus.$emit(this.$event.update_user_info);
              }
            }
          }
      );
    },
    removeOwnerShips(ids) {
      this.$api.adminUserRemoveOwnerShip(ids).then(
          resp => this.getUserItem(this.id)
      );
    }
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
