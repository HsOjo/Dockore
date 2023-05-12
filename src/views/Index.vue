<template>
  <div>
    <Logo></Logo>
    <div class="hint-area">
      <div style="opacity: 0.15; user-select: none">
        <div class="hint-text">⬅️ 点击菜单开始使用。</div>
        <div class="hint-producer">Producer: HsOjo</div>
      </div>
    </div>
  </div>
</template>

<script>
import Logo from "@/components/common/Logo.vue";

export default {
  name: "Index",
  components: {Logo}
}
</script>

<style scoped>
.hint-area {
  display: flex;
  align-items: center;
  height: 392px;
  width: 800px;
}

.hint-text {
  font-size: 64px;
  padding-left: 96px;
  margin-bottom: 16px;
}

.hint-producer {
  text-align: center;
  font-size: 24px;
}

</style>
