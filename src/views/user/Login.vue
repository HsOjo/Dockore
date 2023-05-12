<template>
  <div>
    <el-header>
      <Header></Header>
    </el-header>
    <el-container>
      <Logo></Logo>
      <div style="width: 320px; margin-left: auto; margin-right: auto; padding-top: 64px; text-align: center">
        <h2>用户登录</h2>
        <el-form :model="form" label-position="right">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="（默认：admin）"></el-input>
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" placeholder="（默认：123456）"
                      type="password" @keyup.enter.native="login"></el-input>
          </el-form-item>
          <el-form-item style="float: right">
            <el-dropdown style="margin-right: 8px" trigger="click" @command="handleOperation">
              <el-button>
                指定服务器<i class="el-icon-arrow-down el-icon--right"></i>
              </el-button>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="remote">
                  <el-icon class="el-icon-s-promotion"></el-icon>
                  远程服务器
                </el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
            <el-button v-if="loginAvailable" type="primary" @click="login">登录</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-container>
    <SetServerDialog ref="set_server_dialog"></SetServerDialog>
  </div>
</template>

<script>
import Header from "@/components/common/Header.vue";
import SetServerDialog from "@/components/common/SetServerDialog.vue";
import {mapGetters} from "vuex";
import Logo from "@/components/common/Logo.vue";

export default {
  name: "Login",
  components: {Logo, Header, SetServerDialog},
  computed: {
    ...mapGetters(['isElectron', "serverInfo"]),
    loginAvailable() {
      return !!this.serverInfo
    },
  },
  data() {
    return {
      form: {},
    }
  },
  methods: {
    login() {
      this.$api.userLogin(this.form.username, this.form.password).then(
        resp => {
          let success = resp.code === 0;
          if (success) {
            this.$store.commit('setUserToken', resp.data.token);
            this.$router.push('/');
          }
        }
      )
    },
    handleOperation(cmd) {
      if (cmd === 'remote')
        this.$refs.set_server_dialog.open()
    },
  }
}
</script>

<style scoped>

</style>
