import { createRouter, createWebHistory } from 'vue-router';
import { watch } from 'vue';
import { useAuthStore } from '../stores/auth';
import GoogleAuthCallback from '../components/GoogleAuthCallback.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('../pages/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/plans',
      component: () => import('../pages/plans.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/auth/google/callback',
      component: GoogleAuthCallback
    }
  ]
});

// Navigation guard to check authentication
router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  
  // Skip auth check for Google callback
  if (to.path === '/auth/google/callback') {
    return true;
  }
  
  // Wait for initial auth check if it hasn't completed
  if (authStore.loading) {
    await new Promise<void>((resolve) => {
      const unwatch = watch(authStore, () => {
        if (!authStore.loading) {
          unwatch();
          resolve();
        }
      });
    });
  }

  // Handle protected routes
  if (to.meta.requiresAuth && !authStore.user) {
    return false;
  }

  return true;
});

export default router;