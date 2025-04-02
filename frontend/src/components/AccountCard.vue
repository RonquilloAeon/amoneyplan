<template>
  <div class="mb-2 md:mb-4 bg-base-200 rounded-box">
    <!-- Card Header - Always visible -->
    <div class="p-3 md:p-4 flex justify-between items-start">
      <!-- Left side with account info and progress bar -->
      <div class="flex flex-col gap-1 w-3/5">
        <!-- Account name and total -->
        <div class="flex items-center gap-2">
          <span class="text-lg md:text-xl font-bold text-primary">${{ formattedAccountTotal }}</span>
          <span 
            class="font-medium text-sm md:text-base"
            :class="{ 'line-through opacity-70': isChecked }"
          >
            {{ account.name }}
          </span>
        </div>

        <!-- Progress bar showing percentage of total plan -->
        <div class="w-full">
          <div class="flex justify-between items-center mb-1 text-xs">
            <span>% of Plan</span>
            <span class="font-bold">{{ progressPercentage }}%</span>
          </div>
          <progress 
            class="progress w-full" 
            :class="getProgressBarColor()"
            :value="accountTotal" 
            :max="planInitialBalance"
          ></progress>
        </div>
      </div>

      <!-- Right side with buttons -->
      <div class="flex items-center gap-2">
        <!-- Action buttons -->
        <div class="flex gap-1 mr-2">
          <!-- Edit account notes button -->
          <button 
            v-if="!isArchived" 
            @click.stop="$emit('edit-notes', account)" 
            class="btn btn-ghost btn-xs btn-square"
            title="Edit account notes"
          >
            <i class="fa-solid fa-file-lines text-info"></i>
          </button>
          
          <!-- Edit account button -->
          <button 
            v-if="!isArchived && !isCommitted" 
            @click.stop="$emit('edit-account', account)" 
            class="btn btn-ghost btn-xs btn-square"
            title="Edit account"
          >
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          
          <!-- Delete account button -->
          <button 
            v-if="!isArchived && !isCommitted" 
            @click.stop="$emit('remove-account', account)" 
            class="btn btn-ghost btn-xs btn-square"
            title="Remove account"
          >
            <i class="fa-solid fa-trash-can text-error"></i>
          </button>
        </div>
        
        <!-- Checkmark -->
        <div class="form-control">
          <label 
            class="cursor-pointer hover:bg-base-300 p-1 rounded-md" 
            @click.stop
          >
            <input 
              type="checkbox" 
              :checked="isChecked" 
              @change.stop="$emit('toggle-check', account)" 
              class="checkbox checkbox-sm"
              :disabled="isArchived"
              :class="{ 'checkbox-success': isChecked }"
            />
          </label>
        </div>

        <!-- Toggle button for collapse -->
        <button 
          @click="isOpen = !isOpen"
          class="btn btn-ghost btn-xs"
          :class="{ 'rotate-180': isOpen }"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Collapsible Content -->
    <div v-show="isOpen" class="border-t border-base-300">
      <!-- Account notes if they exist -->
      <div v-if="account.notes" class="px-4 py-3 text-sm text-base-content/80 bg-base-300/30">
        {{ account.notes }}
      </div>
      
      <!-- Only show table if buckets exist -->
      <div v-if="buckets && buckets.length > 0" class="overflow-x-auto p-2">
        <table class="table table-zebra text-xs md:text-sm w-full">
          <thead>
            <tr>
              <th>Bucket Name</th>
              <th>Category</th>
              <th>Allocated Amount</th>
              <th>% of Plan</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bucket in buckets" :key="bucket.id">
              <td>{{ bucket.name }}</td>
              <td>{{ bucket.category }}</td>
              <td>${{ bucket.allocatedAmount.toFixed(2) }}</td>
              <td>{{ calculateBucketPercentage(bucket) }}%</td>
            </tr>
            <!-- Account total row -->
            <tr class="font-semibold border-t">
              <td colspan="2" class="text-right">Account Total:</td>
              <td>${{ formattedAccountTotal }}</td>
              <td>{{ progressPercentage }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="isOpen" class="p-4 text-sm text-base-content/70 italic">
        No buckets available
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Bucket {
  id: string;
  name: string;
  category: string;
  allocatedAmount: number;
}

interface Account {
  id: string;
  name: string;
  type: string;
  notes?: string;
}

const props = defineProps({
  account: {
    type: Object as () => Account,
    required: true
  },
  buckets: {
    type: Array as () => Bucket[],
    required: true
  },
  isChecked: {
    type: Boolean,
    required: true
  },
  planInitialBalance: {
    type: Number,
    required: true
  },
  isArchived: {
    type: Boolean,
    default: false
  },
  isCommitted: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits([
  'toggle-check',
  'edit-notes',
  'edit-account',
  'remove-account'
]);

// Track whether the collapsible section is open
const isOpen = ref(false);

// Calculate the total amount allocated for the account
const accountTotal = computed((): number => {
  if (!props.buckets || !Array.isArray(props.buckets)) {
    return 0;
  }
  return props.buckets.reduce((total, bucket) => total + bucket.allocatedAmount, 0);
});

// Format currency
const formattedAccountTotal = computed((): string => {
  return accountTotal.value.toFixed(2);
});

// Calculate the percentage of the account total relative to the plan initial balance
const progressPercentage = computed((): number => {
  if (props.planInitialBalance <= 0) return 0;
  return Math.round((accountTotal.value / props.planInitialBalance) * 100);
});

// Get the appropriate color class for the progress bar based on the percentage
function getProgressBarColor(): string {
  const percentage = progressPercentage.value;
  if (percentage < 25) return 'progress-accent';
  if (percentage < 50) return 'progress-info';
  if (percentage < 75) return 'progress-success';
  return 'progress-warning';
}

// Calculate the percentage of a bucket's allocated amount relative to the plan initial balance
function calculateBucketPercentage(bucket: Bucket): number {
  if (props.planInitialBalance <= 0) return 0;
  return Math.round((bucket.allocatedAmount / props.planInitialBalance) * 100);
}
</script>

<style scoped>
/* Add any component-specific styles here */
</style>