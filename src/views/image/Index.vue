<template>
  <div>
    <div id="navbar" style="height: 56px">
      <div style="float: left">
        搜索：
        <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px"></el-input>
        <el-switch v-model="is_all" active-text="显示所有镜像" style="margin-left: 16px"></el-switch>
      </div>
      <div style="float: right">
        <el-button v-if="selection.length" type="danger" @click="deleteSelectItems">删除选中</el-button>
        <el-button circle @click="getImageItems">
          <el-icon class="el-icon-refresh"></el-icon>
        </el-button>
        <el-button @click="$refs.pull_dialog.open()">拉取镜像</el-button>
      </div>
    </div>
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
          label="标签"
          width="200">
        <template slot-scope="scope">
          <el-tag v-for="tag in scope.row.tags" :key="tag" closable
                  style="margin-right: 8px; margin-top: 2px; margin-bottom: 2px"
                  type="info" @close="deleteImageItems([tag], true)">{{ tag }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
          label="镜像作者"
          prop="author"
          width="200">
      </el-table-column>
      <el-table-column
          label="创建时间"
          prop="create_time"
          width="160">
      </el-table-column>
      <el-table-column
          label="镜像尺寸"
          prop="size"
          width="120">
      </el-table-column>
      <el-table-column
          fixed="right"
          label="操作"
          width="240">
        <template slot-scope="scope">
          <router-link :to="`/image/${scope.row.id}`" class="el-button el-button--mini">信息</router-link>
          <template v-if="scope.row.tags.length > 1">
            <el-button size="mini" type="danger" @click="deleteImageItems(scope.row.tags)">删除</el-button>
          </template>
          <template v-else>
            <el-button size="mini" type="danger" @click="deleteImageItems([scope.row.id])">删除</el-button>
          </template>
          <el-dropdown style="margin-left: 8px" trigger="click" @command="cmd => handleOperation(scope.row, cmd)">
            <el-button size="mini" type="primary">
              操作<i class="el-icon-arrow-down el-icon--right"></i>
            </el-button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="tag">
                <el-icon class="el-icon-collection-tag"></el-icon>
                标记镜像
              </el-dropdown-item>
              <el-dropdown-item command="history" divided>
                <el-icon class="el-icon-coin"></el-icon>
                镜像历史记录
              </el-dropdown-item>
              <el-dropdown-item command="distribute" divided v-if="$store.getters.isAdmin">
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
    <PullDialog ref="pull_dialog"></PullDialog>
    <HistoryDialog ref="history_dialog"></HistoryDialog>
    <SelectDialog ref="distribute_dialog"></SelectDialog>
  </div>
</template>

<script>
import PullDialog from "@/components/image/PullDialog.vue";
import HistoryDialog from "@/components/image/HistoryDialog.vue";
import SelectDialog from "@/components/admin/user/SelectDialog.vue";

export default {
  name: "Index",
  components: {PullDialog, HistoryDialog, SelectDialog},
  computed: {
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
        if (!item.author)
          item.author = '（未知）';
        item.create_time = this.$moment(item.create_time).from();
        item.size = this.$filesize(item.size);
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
      is_all: false,
    };
  },
  created() {
    this.getImageItems();
    this.$bus.$on(this.$event.refresh_images, () => {
      this.getImageItems()
    })
  },
  beforeDestroy() {
    this.$bus.$off(this.$event.refresh_images);
  },
  watch: {
    is_all(nv, ov) {
      if (nv !== ov)
        this.getImageItems();
    }
  },
  methods: {
    handleSelectionChange(val) {
      this.selection = val;
    },
    handleOperation(item, cmd) {
      if (cmd === 'tag')
        this.tagImageItem(item.id);
      else if (cmd === 'history')
        this.$refs.history_dialog.open(item.id);
      else if (cmd === 'distribute')
        this.distributeItem(item.id);
    },
    distributeItem(id) {
      this.$refs.distribute_dialog.open(
          user_id => {
            this.$api.adminUserDistributeObject(user_id, this.$const.object.TYPE_IMAGE, id).then(
                resp => {
                  if (resp.code === 0)
                    this.$refs.distribute_dialog.close();
                }
            );
          }, '分配镜像对象',
          item => {
            return item.role_type !== this.$const.role.TYPE_ADMIN;
          }
      );
    },
    deleteSelectItems() {
      let ids = [];
      this.selection.map(item => {
        if (item.tags.length > 1)
          for (let tag of item.tags)
            ids.push(tag);
        else
          ids.push(item.id);
      });
      this.deleteImageItems(ids)
    },
    getImageItems() {
      this.$api.imageList(this.is_all).then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      )
    },
    deleteImageItems(ids, tag_only) {
      if (tag_only === undefined)
        tag_only = false;

      this.$api.imageDelete(ids, tag_only).then(
          resp => {
            this.getImageItems();
          }
      );
    },
    tagImageItem(id) {
      this.$prompt('请输入新的镜像标签，格式："[name]:[tag]"。', `标记镜像：${id}`).then(
          ({value}) => {
            let col = value.split(':')
            let name = col, tag = null;
            if (col.length > 1)
              [name, tag] = col;

            this.$api.imageTag(id, name, tag).then(resp => this.getImageItems());
          }
      ).catch(_ => _);
    },
  }
  ,
}
</script>

<style scoped>

</style>
