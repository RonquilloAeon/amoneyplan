<template>
  <div class="flex flex-col sm:flex-row sm:items-center gap-1">
    <span>{{ formatDate(timestamp) }}</span>
    <span class="text-sm text-base-content/70">({{ formatDistanceToNow(timestamp) }} ago)</span>
  </div>
</template>

<script setup lang="ts">
import { formatDistanceToNow as dateFnsFormatDistanceToNow } from 'date-fns';

defineProps<{
  timestamp: string;
}>();

const formatDate = (timestamp: string) => {
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat(undefined, { 
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
  }).format(date);
};

const formatDistanceToNow = (timestamp: string) => {
  return dateFnsFormatDistanceToNow(new Date(timestamp));
};
</script>