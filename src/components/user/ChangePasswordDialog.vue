<template>
  <el-dialog :visible.sync="dialog_visible" title="修改密码" width="480px">
    <el-form :model="form" label-width="120px">
      <el-form-item label="旧密码">
        <el-input v-model="form.old" type="password" placeholder="输入旧密码"></el-input>
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="form.new" type="password" placeholder="新密码"></el-input>
      </el-form-item>
      <el-form-item label="重复新密码">
        <el-input v-model="repeat" type="password" placeholder="重复新密码"></el-input>
      </el-form-item>
    </el-form>
    <span slot="footer" class="dialog-footer">
      <el-button @click="dialog_visible = false">取 消</el-button>
      <el-button type="primary" @click="changePassword"
                 :disabled="!repeat || repeat !== form.new">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: "ChangePasswordDialog",
  data() {
    return {
      dialog_visible: false,
      form: {},
      repeat: '',
    }
  },
  methods: {
    open() {
      this.form = {};
      this.repeat = '';
      this.dialog_visible = true;
    },
    changePassword() {
      this.$api.userChangePassword(this.form.old, this.form.new).then(
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
