<template>
  <div>
    <div style="display: flex; align-items: center; margin: 8px 8px 32px;">
      <el-breadcrumb separator-class="el-icon-arrow-right">
        <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
        <el-breadcrumb-item to="/image">镜像管理</el-breadcrumb-item>
        <el-breadcrumb-item :to="`/image/${item.id}`">
          镜像：{{ item.id }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <el-form :model="item" label-width="120px">
      <el-form-item label="镜像ID">
        <el-input v-model="item.id" readonly></el-input>
      </el-form-item>
      <el-form-item label="标签">
        <el-tag v-for="tag in item.tags" :key="tag" closable style="margin-right: 8px"
                type="info" @close="deleteImageItems([tag], true)">{{ tag }}
        </el-tag>
      </el-form-item>
      <el-form-item label="操作系统">
        <el-input v-model="item.os" readonly></el-input>
      </el-form-item>
      <el-form-item label="镜像作者">
        <el-input v-model="item.author" readonly placeholder="（未知）"></el-input>
      </el-form-item>
      <el-form-item label="启动命令">
        <el-input v-model="item.command" readonly></el-input>
      </el-form-item>
      <el-form-item label="创建时间">
        <el-input v-model="itemCreateTime" readonly></el-input>
      </el-form-item>
      <el-form-item label="镜像尺寸">
        <el-input v-model="itemSize" readonly></el-input>
      </el-form-item>
      <el-form-item>
        <el-checkbox v-model="item.tty" disabled>虚拟终端</el-checkbox>
        <el-checkbox v-model="item.interactive" disabled>交互模式</el-checkbox>
        <el-popover placement="right" style="margin-left: 32px" trigger="click" width="320">
          <el-table :data="item.ports" border>
            <el-table-column label="内部端口" prop="port" width="140"></el-table-column>
            <el-table-column label="协议" prop="protocol" width="140"></el-table-column>
          </el-table>
          <el-button slot="reference" :disabled="item.ports.length === 0">端口映射列表</el-button>
        </el-popover>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
export default {
  name: "Item",
  computed: {
    itemCreateTime() {
      if (this.item.create_time)
        return this.$moment(this.item.create_time).from();
    },
    itemSize() {
      if (this.item.size)
        return this.$filesize(this.item.size);
    },
  },
  data() {
    return {
      item: {tags: [], ports: []},
    }
  },
  created() {
    this.getItemInfo(this.$route.params.id);
  },
  methods: {
    getItemInfo(id) {
      this.$api.imageItem(id).then(
          resp => {
            if (resp.code === 0)
              this.item = resp.data.item;
          }
      )
    },
    deleteImageItems(ids, tag_only) {
      if (tag_only === undefined)
        tag_only = false;

      this.$api.imageDelete(ids, tag_only).then(
          resp => {
            this.getItemInfo(this.item.id);
          }
      );
    },
  }
}
</script>

<style scoped>
.el-form {
  width: 640px;
}
</style>
