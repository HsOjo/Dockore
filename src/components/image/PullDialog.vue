<template>
  <el-dialog :visible.sync="dialog_visible" title="拉取线上镜像" width="1280px">
    <el-container direction="vertical">
      <div id="navbar" style="height: 56px">
        <h2 style="float: left; margin-top: 8px">搜索结果</h2>
        <div style="float: right">
          <el-input v-model="keyword" placeholder="请输入关键字" style="width: 256px" @keyup.enter.native="searchImageItems">
            <el-button slot="append" @click="searchImageItems">
              <i class="el-icon-search"></i>
            </el-button>
          </el-input>
        </div>
      </div>
      <el-table ref="table" :data="tableData" border highlight-current-row
                @current-change="tableCurrentChange">
        <el-table-column
            label="名称"
            prop="name"
            width="200">
        </el-table-column>
        <el-table-column
            label="描述"
            prop="description"
            width="400">
        </el-table-column>
        <el-table-column
            label="Star数"
            prop="star_count"
            width="200">
        </el-table-column>
        <el-table-column
            label="官方镜像"
            width="120">
          <template slot-scope="scope">
            {{ scope.row.is_official ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column
            label="自动构建"
            width="120">
          <template slot-scope="scope">
            {{ scope.row.is_automated ? '支持' : '不支持' }}
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 8px">
        <el-pagination
            :current-page.sync="page" :page-size.sync="page_size"
            :page-sizes="[5, 10, 50, 100]" :total="this.items.length"
            background layout="prev, pager, next, sizes"></el-pagination>
      </div>
    </el-container>
    <span slot="footer" class="dialog-footer">
        <el-input v-model="form.tag" placeholder="版本标签（latest）" style="width: 144px; margin-right: 8px"></el-input>
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="pullImage" :disabled="pull_disabled">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: "PullDialog",
  data() {
    return {
      dialog_visible: false,
      items: [],
      keyword: '',
      page: 1,
      page_size: 10,
      form: {},
      pull_disabled: true,
    };
  },
  computed: {
    tableData() {
      let items = this.items;
      items = items.slice(
          (this.page - 1) * this.page_size,
          this.page * this.page_size
      );

      items = this.$helper.copyObject(items);
      return items;
    },
  },
  methods: {
    open() {
      this.keyword = '';
      this.form = {};
      this.items = [];
      this.dialog_visible = true;
    },

    tableCurrentChange(n, o) {
      if (n) {
        this.form.name = n.name;
        this.pull_disabled = false;
      }
    },

    searchImageItems() {
      if (!this.keyword)
        return

      this.$api.imageSearch(this.keyword).then(
          resp => {
            if (resp.code === 0)
              this.items = resp.data.items;
          }
      )
    },

    pullImage() {
      this.$api.imagePull(this.form.name, this.form.tag).then(
          resp => {
            if (resp.code === 0)
              this.dialog_visible = false;
            this.$bus.$emit(this.$event.refresh_images);
          }
      );
    },
  },
}
</script>

<style scoped>

</style>
