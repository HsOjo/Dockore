<template>
  <div>
    <div id="navbar" style="height: 56px">
      <div style="float: left">
        搜索：
        <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px"></el-input>
      </div>
      <div style="float: right">
        <el-button v-if="selection.length" type="danger" @click="deleteSelectItems">删除选中</el-button>
        <el-button circle @click="getVolumeItems">
          <el-icon class="el-icon-refresh"></el-icon>
        </el-button>
        <el-button @click="$refs.create_dialog.open()">创建存储卷</el-button>
      </div>
    </div>
    <el-table :data="tableData" border @selection-change="handleSelectionChange">
      <el-table-column
          type="selection"
          width="55">
      </el-table-column>
      <el-table-column
          label="名称"
          prop="name"
          width="180">
      </el-table-column>
      <el-table-column
          label="驱动器类型"
          prop="driver"
          width="140">
      </el-table-column>
      <el-table-column
          label="挂载点"
          prop="mount_point"
          width="280">
      </el-table-column>
      <el-table-column
          label="创建时间"
          prop="create_time"
          width="200">
      </el-table-column>
      <el-table-column
          fixed="right"
          label="操作"
          width="240">
        <template slot-scope="scope">
          <router-link :to="`/volume/${scope.row.id}`" class="el-button el-button--mini">信息</router-link>
          <el-button size="mini" type="danger" @click="deleteVolumeItems([scope.row.id])">删除</el-button>
          <el-dropdown style="margin-left: 8px" trigger="click" @command="cmd => handleOperation(scope.row, cmd)"
                       v-if="$store.getters.isAdmin">
            <el-button size="mini" type="primary">
              操作<i class="el-icon-arrow-down el-icon--right"></i>
            </el-button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="distribute">
                <el-icon class="el-icon-share"></el-icon>
                分配对象
              </el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 8px">
      <el-pagination
          :current-page.sync="page" :page-size.sync="page_size"
          :page-sizes="[5, 10, 50, 100]" :total="this.items.length"
          background layout="prev, pager, next, sizes"></el-pagination>
    </div>
    <CreateDialog ref="create_dialog"></CreateDialog>
    <SelectDialog ref="distribute_dialog"></SelectDialog>
  </div>
</template>

<script>
import CreateDialog from "@/components/volume/CreateDialog.vue";
import SelectDialog from "@/components/admin/user/SelectDialog.vue";

export default {
  name: "Index",
  components: {CreateDialog, SelectDialog},
  computed: {
    tableData() {
      let items = this.items;
      if (this.keyword) {
        items = items.filter(item => item.name.indexOf(this.keyword) !== -1 || item.id.indexOf(this.keyword) !== -1);
      }
      items = items.slice(
          (this.page - 1) * this.page_size,
          this.page * this.page_size
      );

      items = this.$helper.copyObject(items);
      for (let item of items) {
        item.driver = this.$text.volume.driver[item.driver];
        item.create_time = this.$moment(item.create_time).from();
      }

      return items;
    },
  },
  data() {
    return {
      items: [],
      selection: [],
      keyword: '',
      page: 1,
      page_size: 10,
    };
  },
  created() {
    this.getVolumeItems();
    this.$bus.$on(this.$event.refresh_volumes, () => {
      this.getVolumeItems()
    })
  },
  beforeDestroy() {
    this.$bus.$off(this.$event.refresh_volumes);
  },
  methods: {
    handleOperation(item, cmd) {
      if (cmd === 'distribute')
        this.distributeItem(item.id);
    },
    distributeItem(id) {
      this.$refs.distribute_dialog.open(
          user_id => {
            this.$api.adminUserDistributeObject(user_id, this.$const.object.TYPE_VOLUME, id).then(
                resp => {
                  if (resp.code === 0)
                    this.$refs.distribute_dialog.close();
                }
            );
          }, '分配存储卷对象',
          item => {
            return item.role_type !== this.$const.role.TYPE_ADMIN;
          }
      );
    },
    handleSelectionChange(val) {
      this.selection = val;
    },
    deleteSelectItems() {
      let ids = [];
      this.selection.map(item => {
        ids.push(item.id);
      });
      this.deleteVolumeItems(ids)
    },
    getVolumeItems() {
      this.$api.volumeList().then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      )
    },
    deleteVolumeItems(ids) {
      this.$api.volumeDelete(ids).then(
          resp => {
            this.getVolumeItems();
          }
      );
    },
  },
}
</script>

<style scoped>

</style>
