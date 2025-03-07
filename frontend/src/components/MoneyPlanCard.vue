<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body p-4 md:p-6">
      <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
        <h2 class="card-title text-base md:text-lg">Plan ID: {{ plan.id }}</h2>
        <div class="badge badge-md md:badge-lg" :class="plan.isCommitted ? 'badge-primary' : 'badge-ghost'">
          {{ plan.isCommitted ? 'Committed' : 'Draft' }}
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
  accounts: Account[];
  isCommitted: boolean;
  initialBalance: number;
  remainingBalance: number;
}

// Define props
defineProps<{
  plan: MoneyPlan
}>();
</script>

<style scoped>
/* Add any scoped styles here */
</style>