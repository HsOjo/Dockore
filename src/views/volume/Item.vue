<template>
  <div>
    <div style="display: flex; align-items: center; margin: 8px 8px 32px;">
      <el-breadcrumb separator-class="el-icon-arrow-right">
        <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
        <el-breadcrumb-item to="/volume">存储卷管理</el-breadcrumb-item>
        <el-breadcrumb-item :to="`/volume/${item.id}`">
          存储卷：{{ item.id }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <el-form :model="item" label-width="120px">
      <el-form-item label="名称">
        <el-input v-model="item.name" readonly></el-input>
      </el-form-item>
      <el-form-item label="驱动器类型">
        <el-input v-model="itemDriver" readonly></el-input>
      </el-form-item>
      <el-form-item label="挂载点">
        <el-input v-model="item.mount_point" readonly></el-input>
      </el-form-item>
      <el-form-item label="范围">
        <el-input v-model="item.scope" readonly></el-input>
      </el-form-item>
      <el-form-item label="创建时间">
        <el-input v-model="itemCreateTime" readonly></el-input>
      </el-form-item>
    </el-form>

    <el-card shadow="hover" style="width: 720px">
      <div slot="header">
        <span>驱动器选项</span>
      </div>
      <el-table :data="itemDriverOptions" border>
        <el-table-column label="键" prop="key" width="320"></el-table-column>
        <el-table-column label="值" prop="value" width="320"></el-table-column>
      </el-table>
    </el-card>
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
    itemDriver() {
      if (this.item.driver)
        return this.$text.$get('volume', 'driver', this.item.driver);
    },
    itemDriverOptions() {
      let result = [];
      let driver_opts = this.item.driver_opts;
      if (driver_opts)
        for (let key in driver_opts)
          result.push({key: key, value: driver_opts[key]})
      return result;
    },
  },
  data() {
    return {
      item: {},
    }
  },
  created() {
    this.getItemInfo(this.$route.params.id);
  },
  methods: {
    getItemInfo(id) {
      this.$api.volumeItem(id).then(
          resp => {
            if (resp.code === 0)
              this.item = resp.data.item;
          }
      )
    },
    deleteVolumeItems(ids) {
      this.$api.volumeDelete(ids).then(
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
