<template>
  <el-dialog :visible.sync="dialog_visible" title="容器文件差异对比" width="1280px">
    <el-input v-model="keyword" placeholder="输入关键字进行过滤" style="margin-bottom: 8px" @keyup.enter.native="searchItem">
      <el-button slot="append" icon="el-icon-search" @click="searchItem"></el-button>
    </el-input>

    <el-tree v-show="!treeEmpty" ref="tree" :data="treeData"
             :default-expanded-keys="['/']" :filter-node-method="filterNode" node-key="label">
      <span slot-scope="{ node, data }"
            style="display: flex; flex: 1; justify-content: space-between; align-items: center">
        <span>
          <el-icon v-if="data.type === 'add'" class="el-icon-circle-plus-outline"></el-icon>
          <el-icon v-else-if="data.type === 'change'" class="el-icon-warning-outline"></el-icon>
          <el-icon v-else-if="data.type === 'delete'" class="el-icon-remove-outline"></el-icon>
          <el-icon v-else-if="data.type === 'other'" class="el-icon-more-outline"></el-icon>
          {{ node.label }}
        </span>
      </span>
    </el-tree>

    <div v-if="treeEmpty" style="margin-top: 128px; margin-bottom: 128px;">
      <h1 style="text-align: center">当前容器无文件改动。</h1>
    </div>
  </el-dialog>
</template>

<script>
export default {
  name: "DiffDialog",
  computed: {
    treeData() {
      let data = [{label: '/', children: [], path: '/'}]

      function addToTree(files, type) {
        let parts, current_node, change;
        for (let file of files) {
          parts = file.split('/').slice(1);
          [current_node] = data;
          let i = 0, dir = '/';
          for (let part of parts) {
            i++;
            change = false;
            for (let child of current_node.children) {
              if (child.label === part) {
                change = true;
                current_node = child;
                break;
              }
            }
            if (!change) {
              let new_node = {label: part, children: [], dir};
              new_node.path = dir + part;
              dir += part + '/';
              current_node.children.push(new_node)
              current_node = new_node;
              if (i >= parts.length)
                new_node.type = type;
            }
          }
        }
      }

      for (let type in this.files)
        addToTree(this.files[type], type);

      return data;
    },
    treeEmpty() {
      return this.treeData[0].children.length === 0
    }
  },
  data() {
    return {
      dialog_visible: false,
      id: '',
      files: {},
      keyword: '',
    }
  },
  methods: {
    open(id) {
      this.id = id;
      this.files = '';
      this.keyword = '';
      this.dialog_visible = true;
      this.checkContainerDiff();
    },
    filterNode(value, data) {
      if (!value) return true;
      return data.path.indexOf(value) !== -1;
    },
    checkContainerDiff() {
      this.$api.containerDiff(this.id).then(
          resp => {
            if (resp.code === 0)
              this.files = resp.data.files;
          }
      );
    },
    searchItem(){
      this.$refs.tree.filter(this.keyword)
    }
  },
}
</script>

<style scoped>

</style>
