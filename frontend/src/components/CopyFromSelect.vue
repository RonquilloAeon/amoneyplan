<template>
  <div class="form-control w-full">
    <div class="dropdown w-full" ref="dropdownRef">
      <div 
        tabindex="0" 
        role="button" 
        class="w-full input input-bordered input-sm md:input-md flex items-center justify-between cursor-pointer"
        :class="{ 'text-base-content/50': !modelValue }"
      >
        <span v-if="!modelValue">Don't copy from previous plan</span>
        <span v-else-if="loading">Loading...</span>
        <span v-else>
          {{ getSelectedPlanDisplay() }}
        </span>
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
      </div>
      <div 
        tabindex="0" 
        class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-full max-h-96 overflow-y-auto flex-nowrap"
      >
        <div 
          role="menuitem"
          class="px-4 py-2 hover:bg-base-200 rounded-lg cursor-pointer"
          :class="{ 'bg-base-200': !modelValue }"
          @click="selectOption('')"
        >
          Don't copy from previous plan
        </div>
        <div v-if="loading" class="text-center py-4">
          <span class="loading loading-spinner loading-sm"></span>
          <span class="ml-2">Loading plans...</span>
        </div>
        <template v-else>
          <div
            v-for="plan in plans"
            :key="plan.id"
            role="menuitem"
            class="px-4 py-2 hover:bg-base-200 rounded-lg cursor-pointer"
            :class="{ 'bg-base-200': modelValue === plan.id }"
            @click="selectOption(plan.id)"
          >
            <div class="flex flex-col">
              <span class="font-medium">
                Plan from {{ formatDate(plan.planDate) }}
                <span class="badge badge-sm ml-2" :class="plan.isCommitted ? 'badge-neutral' : 'badge-ghost'">
                  {{ plan.isCommitted ? 'Committed' : 'Draft' }}
                </span>
              </span>
              <span v-if="plan.notes" class="text-sm text-base-content/70 mt-1">
                {{ plan.notes }}
              </span>
            </div>
          </div>
          <div
            v-if="hasMorePlans"
            class="px-4 py-2 text-center hover:bg-base-200 rounded-lg cursor-pointer"
            @click="loadMore"
          >
            <span v-if="loadingMore" class="loading loading-spinner loading-xs mr-2"></span>
            Load more plans...
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useQuery } from '@urql/vue';
import { PLANS_FOR_COPY } from '../graphql/queries';

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

interface Plan {
  id: string;
  planDate: string;
  notes: string;
  isCommitted: boolean;
}

const plans = ref<Plan[]>([]);
const loadingMore = ref(false);
const dropdownRef = ref<HTMLElement | null>(null);

const { data, fetching: loading, executeQuery } = useQuery({
  query: PLANS_FOR_COPY,
  variables: { first: 10 },
  pause: true, // Don't fetch immediately
});

const hasMorePlans = computed(() => {
  return data.value?.moneyPlans.pageInfo.hasNextPage || false;
});

// Format date using the same format as PlanDate component
const formatDate = (planDate: string | undefined) => {
  if (!planDate) return "Date unavailable";
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

// Get the display text for the selected plan
const getSelectedPlanDisplay = () => {
  const selectedPlan = plans.value.find(p => p.id === props.modelValue);
  if (!selectedPlan) return '';
  return `Plan from ${formatDate(selectedPlan.planDate)}`;
};

// Handle option selection
const selectOption = (value: string) => {
  if (value !== props.modelValue) {
    // Only emit if the value is different
    emit('update:modelValue', value);
  }
  
  // Close the dropdown if we're not clicking "Load more"
  if (dropdownRef.value && !loadingMore.value) {
    // Remove focus from the dropdown elements
    const dropdownElements = dropdownRef.value.querySelectorAll('[tabindex="0"]');
    dropdownElements.forEach(el => {
      (el as HTMLElement).blur();
    });
  }
};

// Load more plans when scrolling
const loadMore = async () => {
  if (!hasMorePlans.value || loadingMore.value) return;
  
  loadingMore.value = true;
  try {
    await executeQuery({
      variables: {
        first: 10,
        after: data.value.moneyPlans.pageInfo.endCursor,
      }
    });
  } finally {
    loadingMore.value = false;
  }
};

// Watch for data changes and update plans array
watch(() => data.value?.moneyPlans.edges, (newEdges) => {
  if (newEdges) {
    const newPlans = newEdges.map((edge: any) => edge.node);
    plans.value = [...plans.value, ...newPlans];
  }
}, { deep: true });

onMounted(() => {
  executeQuery(); // Initial load of plans
});
</script>

<style scoped>
/* Ensure dropdown menu takes full width of parent */
.dropdown .dropdown-content {
  width: 100%;
}

/* Custom scrollbar styles */
.dropdown-content::-webkit-scrollbar {
  width: 6px;
}

.dropdown-content::-webkit-scrollbar-track {
  background: transparent;
}

.dropdown-content::-webkit-scrollbar-thumb {
  background-color: hsl(var(--bc) / 0.2);
  border-radius: 3px;
}

.dropdown-content::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--bc) / 0.3);
}
</style>