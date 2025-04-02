<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, RouterView, useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';
import LoginForm from './components/LoginForm.vue';
import RegisterForm from './components/RegisterForm.vue';
import PageHeader from './components/PageHeader.vue';
import type { User } from './stores/auth';

const showLogin = ref(true);
const authStore = useAuthStore();
const router = useRouter();

async function handleAuthSuccess(user: User) {
  await authStore.setUser(user);
  router.push('/');
}

async function handleLogout() {
  await authStore.handleLogout();
  router.push('/');
}
</script>

<template>
  <div class="app">
    <template v-if="authStore.loading">
      <div class="loading">Loading...</div>
    </template>
    <template v-else-if="!authStore.user">
      <LoginForm
        v-if="showLogin"
        @auth-success="handleAuthSuccess"
        @switch-to-register="showLogin = false"
      />
      <RegisterForm
        v-else
        @auth-success="handleAuthSuccess"
        @switch-to-login="showLogin = true"
      />
    </template>
    <template v-else>
      <header>
        <PageHeader>
          <template #right>
            <div class="user-info">
              Welcome, {{ authStore.user.firstName }}
              <button @click="handleLogout" class="logout-btn">Logout</button>
            </div>
          </template>
        </PageHeader>
      </header>
      <div class="drawer">
        <input id="my-drawer" type="checkbox" class="drawer-toggle" />
        <div class="drawer-content">
          <!-- Navbar -->
          <div class="navbar bg-base-100 shadow-md rounded-box mb-4 px-2">
            <div class="navbar-start">
              <div class="lg:hidden">
                <label for="my-drawer" class="btn btn-square btn-ghost">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-5 h-5 stroke-current"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                </label>
              </div>
              <a href="#" class="text-xl font-semibold">Money Planner</a>
            </div>
            <div class="navbar-center hidden lg:flex">
              <ul class="menu menu-horizontal px-1">
                <li><RouterLink to="/" class="font-medium">Make a plan</RouterLink></li>
                <li><RouterLink to="/plans" class="font-medium">Plans</RouterLink></li>
              </ul>
            </div>
            <div class="navbar-end">
            </div>
          </div>
          
          <!-- Page content container with responsive padding -->
          <div class="container mx-auto px-2 sm:px-4 md:px-6 lg:px-8">
            <router-view />
          </div>
        </div>
        
        <!-- Mobile drawer -->
        <div class="drawer-side z-40">
          <label for="my-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
          <ul class="menu p-4 w-64 min-h-full bg-base-200">
            <li class="mb-4"><span class="text-lg font-bold">Money Planner</span></li>
            <li><RouterLink to="/" class="font-medium">Make a plan</RouterLink></li>
            <li><RouterLink to="/plans" class="font-medium">Plans</RouterLink></li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background-color: #dc2626;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-btn:hover {
  background-color: #b91c1c;
}
</style>
