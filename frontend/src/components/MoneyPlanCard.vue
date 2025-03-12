<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body p-4 md:p-6">
      <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
        <h2 class="card-title text-base md:text-lg">
          <PlanDate :timestamp="plan.timestamp" />
        </h2>
        <div class="flex gap-2 items-center">
          <div class="badge badge-md md:badge-lg" :class="getBadgeClass()">
            {{ getPlanStatus() }}
          </div>
          <button 
            v-if="!plan.isArchived" 
            @click="archivePlan" 
            class="btn btn-sm btn-square btn-ghost"
            :class="{'loading': isArchiving}"
            :disabled="isArchiving"
            title="Archive plan"
          >
            <svg v-if="!isArchiving" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
              <path stroke-linecap="round" stroke-linejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m8.25 3v6.75m0-6.75h-3m3 0h3M12 3v1.5m-2.25 0h4.5" />
            </svg>
          </button>
        </div>
      </div>
      
      <div class="stats shadow my-2 md:my-4 stats-vertical md:stats-horizontal">
        <div class="stat p-2 md:p-4">
          <div class="stat-title text-xs md:text-sm">Initial Balance</div>
          <div class="stat-value text-primary text-lg md:text-2xl">${{ plan.initialBalance }}</div>
        </div>
        
        <div class="stat p-2 md:p-4">
          <div class="stat-title text-xs md:text-sm">Remaining Balance</div>
          <div class="stat-value text-lg md:text-2xl" :class="plan.remainingBalance > 0 ? 'text-success' : 'text-error'">
            ${{ plan.remainingBalance }}
          </div>
        </div>
      </div>
      
      <div class="divider my-1 md:my-2">Accounts</div>
      
      <div v-for="account in plan.accounts" :key="account.name" class="mb-2 md:mb-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" /> 
          <div class="collapse-title font-medium py-2 md:py-3 text-sm md:text-base">
            Account: {{ account.name }}
          </div>
          <div class="collapse-content p-0 md:p-2">
            <div class="overflow-x-auto">
              <table class="table table-zebra text-xs md:text-sm w-full">
                <thead>
                  <tr>
                    <th>Bucket Name</th>
                    <th>Allocated Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="bucket in account.buckets" :key="bucket.bucketName">
                    <td>{{ bucket.bucketName }}</td>
                    <td>${{ bucket.allocatedAmount }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMutation } from '@urql/vue';
import PlanDate from './PlanDate.vue';

interface Bucket {
  bucketName: string;
  allocatedAmount: number;
}

interface Account {
  name: string;
  buckets: Bucket[];
}

interface MoneyPlan {
  id: string;
  timestamp: string;
  accounts: Account[];
  isCommitted: boolean;
  isArchived: boolean;
  initialBalance: number;
  remainingBalance: number;
}

const props = defineProps<{
  plan: MoneyPlan
}>();

const emit = defineEmits(['planArchived']);

const isArchiving = ref(false);

const ARCHIVE_PLAN_MUTATION = `
  mutation archivePlan($input: ArchivePlanInput!) {
    moneyPlan {
      archivePlan(input: $input) {
        success
        error {
          message
        }
        moneyPlan {
          id
          isArchived
        }
      }
    }
  }
`;

const { executeMutation } = useMutation(ARCHIVE_PLAN_MUTATION);

function getBadgeClass() {
  if (props.plan.isArchived) return 'badge-ghost';
  return props.plan.isCommitted ? 'badge-primary' : 'badge-ghost';
}

function getPlanStatus() {
  if (props.plan.isArchived) return 'Archived';
  return props.plan.isCommitted ? 'Committed' : 'Draft';
}

async function archivePlan() {
  if (isArchiving.value) return;
  
  isArchiving.value = true;
  try {
    const result = await executeMutation({
      input: {
        planId: props.plan.id
      }
    });

    if (result.error) {
      console.error('Error archiving plan:', result.error);
      return;
    }

    if (result.data?.moneyPlan?.archivePlan?.success) {
      emit('planArchived', result.data.moneyPlan.archivePlan.moneyPlan);
    } else {
      console.error('Failed to archive plan:', result.data?.moneyPlan?.archivePlan?.error?.message);
    }
  } catch (e) {
    console.error('Error archiving plan:', e);
  } finally {
    isArchiving.value = false;
  }
}
</script>