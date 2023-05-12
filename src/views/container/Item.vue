<template>
  <div>
    <div style="display: flex; align-items: center; margin: 8px 8px 16px;">
      <el-breadcrumb separator-class="el-icon-arrow-right">
        <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
        <el-breadcrumb-item to="/container">容器管理</el-breadcrumb-item>
        <el-breadcrumb-item :to="`/container/${item.id}`">
          容器：{{ item.name }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="基本信息" name="basic">
        <el-form :model="item" label-width="120px" style="width: 640px">
          <el-form-item label="容器ID">
            <el-input v-model="item.id" readonly></el-input>
          </el-form-item>
          <el-form-item label="容器名称">
            <el-input v-model="item.name">
              <el-button slot="append" @click="renameContainerItem">
                <el-icon class="el-icon-edit"></el-icon>
              </el-button>
            </el-input>
          </el-form-item>
          <el-form-item label="镜像ID">
            <el-input v-model="item.image.id" readonly>
              <router-link class="el-link" slot="append" :to="`/image/${item.image.id}`">
                <el-icon class="el-icon-right"></el-icon>
              </router-link>
            </el-input>
          </el-form-item>
          <el-form-item label="启动命令">
            <el-input v-model="item.command" readonly></el-input>
          </el-form-item>
          <el-form-item label="创建时间">
            <el-input v-model="itemCreateTime" readonly></el-input>
          </el-form-item>
          <el-form-item label="状态">
            <el-input v-model="itemStatus" readonly></el-input>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="item.tty" disabled>虚拟终端</el-checkbox>
            <el-checkbox v-model="item.interactive" disabled>交互模式</el-checkbox>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="网络信息" name="network">
        <el-form :model="item.network" label-width="120px" style="width: 640px">
          <el-form-item label="IP">
            <el-input v-model="item.network.ip" placeholder="未启动" readonly></el-input>
          </el-form-item>
          <el-form-item label="前缀">
            <el-input v-model="item.network.prefix" readonly></el-input>
          </el-form-item>
          <el-form-item label="网关">
            <el-input v-model="item.network.gateway" readonly></el-input>
          </el-form-item>
          <el-form-item label="MAC地址">
            <el-input v-model="item.network.mac_address" readonly></el-input>
          </el-form-item>
        </el-form>
        <el-card shadow="hover" style="width: 720px">
          <div slot="header">
            <span>端口映射列表</span>
          </div>
          <el-table :data="item.network.ports" border>
            <el-table-column label="内部端口" prop="port" width="140"></el-table-column>
            <el-table-column label="协议" prop="protocol" width="140"></el-table-column>
            <el-table-column label="监听地址" prop="listen_ip" width="200"></el-table-column>
            <el-table-column label="监听端口" prop="listen_port" width="140"></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="存储信息" name="volume">
        <el-card shadow="hover" style="width: 1100px">
          <div slot="header">
            <span>存储挂载列表</span>
          </div>
          <el-table :data="item.mounts" border>
            <el-table-column label="存储类型" width="120">
              <template slot-scope="scope">
                {{ mountType(scope.row.type) }}
              </template>
            </el-table-column>
            <el-table-column label="存储卷名称" width="200">
              <template slot-scope="scope">
                <router-link class="el-button el-button--mini" v-if="scope.row.name"
                             :to="`/volume/${scope.row.name}`">
                  {{ scope.row.name }}
                </router-link>
                <template v-else>（无）</template>
              </template>
            </el-table-column>
            <el-table-column label="驱动器类型" width="120">
              <template slot-scope="scope">
                {{ volumeDriver(scope.row.driver) || '（文件）' }}
              </template>
            </el-table-column>
            <el-table-column label="挂载模式" width="120">
              <template slot-scope="scope">
                {{ mountMode(scope.row.mode) }}
              </template>
            </el-table-column>
            <el-table-column label="挂载源" width="240">
              <template slot-scope="scope">
                {{ scope.row.src }}
              </template>
            </el-table-column>
            <el-table-column label="挂载目标" width="240">
              <template slot-scope="scope">
                {{ scope.row.dest }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
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
    itemStatus() {
      let status = this.item.status;
      if (status)
        return this.$text.$get('container', 'status', status);
    },
    mountMode() {
      return k => this.$text.$get('volume', 'mount_mode', k);
    },
    volumeDriver() {
      return k => this.$text.$get('volume', 'driver', k);
    },
    mountType() {
      return k => this.$text.$get('volume', 'mount_type', k);
    },
  },
  data() {
    return {
      tab: 'basic',
      item: {image: {}, network: {}, mounts: []},
    }
  },
  created() {
    this.getItemInfo(this.$route.params.id);
  },
  methods: {
    getItemInfo(id) {
      this.$api.containerItem(id).then(
          resp => {
            if (resp.code === 0)
              this.item = resp.data.item;
          }
      )
    },
    renameContainerItem() {
      this.$api.containerRename(this.item.id, this.item.name).then(
          () => this.getItemInfo(this.item.id)
      );
    },
  }
}
</script>

<style scoped>
.el-tab-pane {
  padding-top: 16px;
  padding-left: 16px;
}

.el-tabs {
  padding-left: 16px;
}
</style>
