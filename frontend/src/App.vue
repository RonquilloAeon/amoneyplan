<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink } from 'vue-router';
</script>

<template>
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

<style scoped>
/* Add any scoped styles here */
</style>
