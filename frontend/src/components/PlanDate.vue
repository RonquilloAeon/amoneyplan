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

const formatDate = (timestamp: string | undefined) => {
  if (!timestamp) {
    return "Date unavailable";
  }
  try {
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat(undefined, { 
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    }).format(date);
  } catch (error) {
    console.error("Error formatting date:", error);
    return "Invalid date";
  }
};

const formatDistanceToNow = (timestamp: string | undefined) => {
  if (!timestamp) {
    return "unknown time";
  }
  try {
    return dateFnsFormatDistanceToNow(new Date(timestamp));
  } catch (error) {
    console.error("Error calculating distance:", error);
    return "unknown time";
  }
};
</script>