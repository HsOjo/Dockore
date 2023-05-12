<template>
  <el-dialog :visible.sync="dialog_visible" title="提交容器改动到镜像" width="560px">
    <el-form :model="form" label-width="120px" style="padding-right: 48px">
      <el-form-item label="镜像名称">
        <el-input v-model="form.name"></el-input>
      </el-form-item>
      <el-form-item label="镜像标签">
        <el-input v-model="form.tag" placeholder="latest"></el-input>
      </el-form-item>
      <el-form-item label="作者名称">
        <el-input v-model="form.author"></el-input>
      </el-form-item>
      <el-form-item label="提交消息">
        <el-input v-model="form.message" :autosize="{ minRows: 5, maxRows: 10 }" type="textarea"></el-input>
      </el-form-item>
    </el-form>
    <span slot="footer" class="dialog-footer">
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="commitContainer">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: "CommitDialog",
  data() {
    return {
      dialog_visible: false,
      form: {},
    }
  },
  methods: {
    open(id) {
      this.form = {id}
      this.dialog_visible = true;
    },
    commitContainer() {
      this.$api.containerCommit(this.form.id, this.form.name, this.form.tag, this.form.message, this.form.author).then(
          resp => {
            if (resp.code === 0)
              this.dialog_visible = false;
          }
      );
    }
  }
}
</script>

<style scoped>

</style>
