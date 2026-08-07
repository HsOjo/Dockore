import { createRouter, createWebHistory } from "vue-router";
import { useConnectionStore } from "@/stores";
import { hasUISettings } from "@/platform";

const routes = [
  {
    path: "/",
    component: () => import("@/layouts/MainLayout.vue"),
    meta: { requiresAuth: true },
    redirect: "/containers",
    children: [
      { path: "containers", component: () => import("@/views/container/Index.vue") },
      { path: "containers/:id", component: () => import("@/views/container/Detail.vue") },
      { path: "containers/:id/terminal", component: () => import("@/views/container/Terminal.vue") },
      { path: "images", component: () => import("@/views/image/Index.vue") },
      { path: "images/:id", component: () => import("@/views/image/Detail.vue") },
      { path: "networks", component: () => import("@/views/network/Index.vue") },
      { path: "networks/:id", component: () => import("@/views/network/Detail.vue") },
      { path: "volumes", component: () => import("@/views/volume/Index.vue") },
      { path: "volumes/:id", component: () => import("@/views/volume/Detail.vue") },
      { path: "system", component: () => import("@/views/system/Version.vue") },
      { path: "settings", component: () => import("@/views/Settings.vue") },
    ],
  },
  {
    path: "/onboarding",
    component: () => import("@/views/Onboarding.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

let initGuarded = false;

router.beforeEach(async (to, _from, next) => {
  const conn = useConnectionStore();
  if (!initGuarded) {
    initGuarded = true;
    await conn.init();
  }

  // The welcome flow is only required on first launch, when the user has not
  // yet configured the UI settings (language / theme).
  if (!hasUISettings()) {
    if (to.path !== "/onboarding") {
      return next("/onboarding");
    }
    return next();
  }

  // If the saved server is unreachable, stay on onboarding so the user can
  // reconnect instead of landing on a broken home page.
  if (!conn.isReady) {
    if (to.path !== "/onboarding") {
      return next("/onboarding");
    }
    return next();
  }

  if (conn.isReady && to.path === "/onboarding") {
    return next("/");
  }

  next();
});

export default router;
