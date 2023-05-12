<template>
  <div>
    <div style="height: 56px">
      <div style="float: left">
        搜索：
        <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px"></el-input>
        <el-switch v-model="is_all" active-text="显示所有容器" style="margin-left: 16px"></el-switch>
      </div>
      <div style="float: right">
        <el-button-group style="margin-right: 16px">
          <el-button v-if="selection.length" type="info" @click="stopContainerItems(selectionIds)">
            <el-icon class="el-icon-video-pause"></el-icon>
            停止
          </el-button>
          <el-button v-if="selection.length" type="warning" @click="restartContainerItems(selectionIds)">
            <el-icon class="el-icon-refresh-right"></el-icon>
            重启
          </el-button>
          <el-button v-if="selection.length" type="success" @click="startContainerItems(selectionIds)">
            <el-icon class="el-icon-video-play"></el-icon>
            启动
          </el-button>
          <el-button v-if="selection.length" type="danger" @click="deleteContainerItems(selectionIds)">
            <el-icon class="el-icon-delete"></el-icon>
            删除
          </el-button>
        </el-button-group>
        <el-button circle @click="getContainerItems">
          <el-icon class="el-icon-refresh"></el-icon>
        </el-button>
        <el-button @click="$refs.create_dialog.open()">创建容器</el-button>
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
          label="名称"
          prop="name"
          width="160">
      </el-table-column>
      <el-table-column
          label="镜像"
          width="240">
        <template slot-scope="scope">
          <router-link v-if="!scope.row.image.tags.length" :to="`/image/${scope.row.image.id}`">
            {{ scope.row.image.id }}
          </router-link>
          <router-link v-else v-for="tag in scope.row.image.tags" :key="tag" :to="`/image/${scope.row.image.id}`"
                       style="margin-top: 2px; margin-bottom: 2px"
                       class="el-button el-button--mini">{{ tag }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column
          label="创建时间"
          prop="create_time"
          width="160">
      </el-table-column>
      <el-table-column
          label="状态"
          prop="status_"
          width="120">
      </el-table-column>
      <el-table-column
          fixed="right"
          label="操作"
          width="240">
        <template slot-scope="scope">
          <router-link :to="`/container/${scope.row.id}`" class="el-button el-button--mini">信息</router-link>
          <el-button size="mini" type="info" v-show="scope.row.is_running"
                     @click="stopContainerItems([scope.row.id])">停止
          </el-button>
          <el-button size="mini" type="danger" v-show="!scope.row.is_running"
                     @click="deleteContainerItems([scope.row.id])">删除
          </el-button>
          <el-dropdown style="margin-left: 8px" trigger="click" @command="cmd => handleOperation(scope.row, cmd)">
            <el-button size="mini" type="primary">
              操作<i class="el-icon-arrow-down el-icon--right"></i>
            </el-button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename">
                <el-icon class="el-icon-edit"></el-icon>
                容器更名
              </el-dropdown-item>
              <el-dropdown-item command="logs" divided>
                <el-icon class="el-icon-tickets"></el-icon>
                容器操作日志
              </el-dropdown-item>
              <el-dropdown-item command="diff">
                <el-icon class="el-icon-document-checked"></el-icon>
                文件差异对比
              </el-dropdown-item>
              <el-dropdown-item command="commit">
                <el-icon class="el-icon-s-promotion"></el-icon>
                提交到镜像
              </el-dropdown-item>
              <el-dropdown-item divided command="start" :disabled="scope.row.is_running">
                <el-icon class="el-icon-video-play"></el-icon>
                启动容器
              </el-dropdown-item>
              <el-dropdown-item command="stop" :disabled="!scope.row.is_running">
                <el-icon class="el-icon-circle-close"></el-icon>
                停止容器
              </el-dropdown-item>
              <el-dropdown-item command="restart">
                <el-icon class="el-icon-refresh-right"></el-icon>
                重启容器
              </el-dropdown-item>
              <el-dropdown-item divided command="terminal" :disabled="!scope.row.is_running">
                <el-icon class="el-icon-s-platform"></el-icon>
                容器终端交互
              </el-dropdown-item>
              <el-dropdown-item command="exec" :disabled="!scope.row.is_running">
                <el-icon class="el-icon-magic-stick"></el-icon>
                容器命令执行
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
    <CreateDialog ref="create_dialog"></CreateDialog>
    <LogsDialog ref="logs_dialog"></LogsDialog>
    <DiffDialog ref="diff_dialog"></DiffDialog>
    <CommitDialog ref="commit_dialog"></CommitDialog>
    <SelectDialog ref="distribute_dialog"></SelectDialog>
  </div>
</template>

<script>
import CreateDialog from "@/components/container/CreateDialog.vue";
import LogsDialog from "@/components/container/LogsDialog.vue";
import DiffDialog from "@/components/container/DiffDialog.vue";
import CommitDialog from "@/components/container/CommitDialog.vue";
import SelectDialog from "@/components/admin/user/SelectDialog.vue";

export default {
  name: "Index",
  components: {CommitDialog, CreateDialog, LogsDialog, DiffDialog, SelectDialog},
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
        item.status_ = this.$text.$get('container', 'status', item.status);
        item.create_time = this.$moment(item.create_time).from();
        item.is_running = item.status === 'running';
      }
      return items;
    },
    selectionIds() {
      return this.selection.map(items => items.id);
    }
  },
  data() {
    return {
      items: [],
      is_all: true,
      selection: [],
      keyword: '',
      page: 1,
      page_size: 10,
    };
  },
  created() {
    this.getContainerItems();
    this.$bus.$on(this.$event.refresh_containers, () => {
      this.getContainerItems()
    })
  },
  beforeDestroy() {
    this.$bus.$off(this.$event.refresh_containers);
  },
  watch: {
    is_all(nv, ov) {
      if (nv !== ov)
        this.getContainerItems();
    }
  },
  methods: {
    handleSelectionChange(val) {
      this.selection = val;
    },
    handleOperation(item, cmd) {
      if (cmd === 'start')
        this.startContainerItems([item.id]);
      else if (cmd === 'stop')
        this.stopContainerItems([item.id]);
      else if (cmd === 'restart')
        this.restartContainerItems([item.id]);
      else if (cmd === 'rename')
        this.renameContainerItem(item);
      else if (cmd === 'logs')
        this.$refs.logs_dialog.open(item.id);
      else if (cmd === 'diff')
        this.$refs.diff_dialog.open(item.id)
      else if (cmd === 'commit')
        this.$refs.commit_dialog.open(item.id)
      else if (cmd === 'terminal')
        this.openContainerTerminal(item.id);
      else if (cmd === 'exec')
        this.execCommandContainer(item);
      else if (cmd === 'distribute')
        this.distributeItem(item.id);
    },
    distributeItem(id) {
      this.$refs.distribute_dialog.open(
          user_id => {
            this.$api.adminUserDistributeObject(user_id, this.$const.object.TYPE_CONTAINER, id).then(
                resp => {
                  if (resp.code === 0)
                    this.$refs.distribute_dialog.close();
                }
            );
          }, '分配容器对象',
          item => {
            return item.role_type !== this.$const.role.TYPE_ADMIN;
          }
      );
    },
    getContainerItems() {
      this.$api.containerList(this.is_all).then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      );
    },
    deleteContainerItems(ids) {
      this.$api.containerDelete(ids).then(
          resp => this.getContainerItems()
      );
    },
    startContainerItems(ids) {
      this.$api.containerStart(ids).then(
          resp => this.getContainerItems()
      );
    },
    stopContainerItems(ids) {
      this.$api.containerStop(ids, 5).then(
          resp => {
            this.getContainerItems();
          }
      );
    },
    restartContainerItems(ids) {
      this.$api.containerRestart(ids, 5).then(
          resp => {
            this.getContainerItems();
          }
      );
    },
    renameContainerItem(item) {
      this.$prompt('请输入新的容器名称', `容器更名：${item.name}`).then(
          ({value}) => {
            this.$api.containerRename(item.id, value).then(resp => this.getContainerItems())
          }
      ).catch(_ => _);
    },
    openContainerTerminal(id, command) {
      this.$api.containerTerminal(id, command).then(
          resp => {
            if (resp.code === 0) {
              let token = resp.data.token;
              this.$router.push(`/container/terminal/${token}`)
            }
          }
      )
    },
    execCommandContainer(item) {
      this.$prompt('请输入需要在终端执行的命令', `执行命令：${item.name}`).then(
          ({value}) => {
            this.openContainerTerminal(item.id, value);
          }
      ).catch(_ => _);
    }
  },
}
</script>

<style scoped>

</style>
