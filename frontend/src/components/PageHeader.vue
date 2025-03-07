<template>
  <div class="hero bg-base-100 shadow-lg mb-6">
    <div class="hero-content" :class="centered ? 'text-center' : ''">
      <div class="py-4 md:py-8">
        <h1 class="text-2xl md:text-3xl font-bold">{{ title }}</h1>
        <p v-if="subtitle" class="py-1 md:py-2 text-sm md:text-base">{{ subtitle }}</p>
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
  centered?: boolean;
}>();
</script>

<style scoped>
/* Add any scoped styles here */
</style>