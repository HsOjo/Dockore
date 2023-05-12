<template>
  <div>
    <el-header>
      <Header></Header>
    </el-header>
    <el-container>
      <el-aside v-if="isLogined" style="width: auto">
        <LeftASide></LeftASide>
      </el-aside>
      <el-main class="content">
        <router-view/>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import Header from "@/components/common/Header.vue";
import LeftASide from "@/components/common/LeftASide.vue";

export default {
  name: "Home",
  components: {Header, LeftASide},
  computed: {
    isLogined() {
      return this.$store.getters.userToken;
    },
  },
  created() {
    this.$bus.$on(this.$event.update_user_info, this.updateUserInfo);
    if (this.isLogined) {
      this.updateUserInfo();
    } else {
      this.$router.push('/login');
    }
  },
  beforeDestroy() {
    this.$bus.$off(this.$event.update_user_info);
  },
  methods: {
    updateUserInfo() {
      this.$api.userInfo().then(
          resp => {
            if (!resp.code) {
              this.$store.commit('setUserInfo', resp.data);
            } else {
              this.$router.push('/login');
            }
          }
      )
    }
  }
}
</script>

<style scoped>
.content {
  /* 100% - Header - Border */
  height: calc(100vh - 60px - 1px);
  margin-top: 1px;
}
</style>
