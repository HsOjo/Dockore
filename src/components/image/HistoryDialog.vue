<template>
  <el-dialog :visible.sync="dialog_visible" title="镜像历史记录" width="1280px">
    <el-table :data="tableData" border>
      <el-table-column
          label="ID"
          width="160">
        <template slot-scope="scope">
          <template v-if="scope.row.id === '<missing>'">{{ scope.row.id }}</template>
          <router-link v-else class="el-button el-button--mini" :to="`/image/${scope.row.id}`">
            {{ scope.row.id }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column
          label="标签"
          width="240">
        <template slot-scope="scope">
          <el-tag v-for="tag in scope.row.tags" :key="tag" type="info">{{ tag }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column
          label="提交信息"
          prop="comment"
          width="320">
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
      <el-table-column
          fixed="right"
          label="创建指令"
          width="120">
        <template slot-scope="scope">
          <el-popover
              :content="scope.row.created_by"
              placement="left-start"
              title="创建指令"
              trigger="hover"
              width="320">
            <el-button slot="reference" size="mini">查看</el-button>
          </el-popover>
        </template>
      </el-table-column>
    </el-table>
  </el-dialog>
</template>

<script>
export default {
  name: "HistoryDialog",
  computed: {
    tableData() {
      let items = this.histories;

      items = this.$helper.copyObject(items);
      for (let item of items) {
        item.create_time = this.$moment(item.create_time).from();
        item.size = this.$filesize(item.size);
      }

      return items;
    }
  },
  data() {
    return {
      dialog_visible: false,
      histories: [],
    }
  },
  methods: {
    open(id) {
      this.dialog_visible = true;
      this.catchImageHistory(id);
    },
    catchImageHistory(id) {
      this.$api.imageHistory(id).then(
          resp => {
            if (resp.code === 0)
              this.histories = resp.data.histories;
          }
      );
    }
  }
}
</script>

<style scoped>

</style>
