<template>
  <div class="flex flex-col sm:flex-row sm:items-center gap-1">
    <span>{{ formatDate(planDate) }}</span>
    <span class="text-sm text-base-content/70">({{ formatDistanceToNow(planDate) }} ago)</span>
  </div>
</template>

<script setup lang="ts">
import { formatDistanceToNow as dateFnsFormatDistanceToNow } from 'date-fns';

defineProps<{
  planDate: string;
}>();

const formatDate = (planDate: string | undefined) => {
  if (!planDate) {
    return "Date unavailable";
  }
  try {
    const date = new Date(planDate);
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

const formatDistanceToNow = (planDate: string | undefined) => {
  if (!planDate) {
    return "unknown time";
  }
  try {
    return dateFnsFormatDistanceToNow(new Date(planDate));
  } catch (error) {
    console.error("Error calculating distance:", error);
    return "unknown time";
  }
};
</script>