<template>
  <div class="min-h-screen bg-base-200">
    <!-- Hero section with title -->
    <div class="hero bg-base-100 shadow-lg mb-6">
      <div class="hero-content text-center py-4 md:py-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold">Money Plans</h1>
          <p class="py-1 md:py-2 text-sm md:text-base">Manage your finances with smart money plans</p>
        </div>
      </div>
    </div>

    <div class="container mx-auto pb-8">
      <!-- Action Button with responsive positioning -->
      <div class="flex justify-center sm:justify-end mb-4 px-4">
        <button @click="showStartPlanDialog = true" class="btn btn-primary btn-sm md:btn-md">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 md:w-5 md:h-5 mr-1 md:mr-2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Start New Plan
        </button>
      </div>
      
      <!-- Money Plans List with responsive grid -->
      <div class="grid gap-4 md:gap-6 px-3">
        <div v-if="moneyPlans.length === 0" class="card bg-base-100 shadow-xl">
          <div class="card-body text-center py-6 md:py-10">
            <h2 class="card-title justify-center text-lg md:text-xl">No Money Plans Yet</h2>
            <p class="text-sm md:text-base">Click the "Start New Plan" button to create your first plan.</p>
          </div>
        </div>
        
        <div v-for="plan in moneyPlans" :key="plan.id" class="card bg-base-100 shadow-xl">
          <div class="card-body p-4 md:p-6">
            <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
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
      </div>
    </div>
    
    <StartPlanDialog v-if="showStartPlanDialog" @close="showStartPlanDialog = false" @planCreated="addPlan" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watchEffect } from 'vue';
import { useQuery } from '@urql/vue';
import StartPlanDialog from '../components/StartPlanDialog.vue';
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
const showStartPlanDialog = ref(false);
const moneyPlans = ref<MoneyPlan[]>([]);
const GET_MONEY_PLANS = `
  query moneyPlans {
    moneyPlans {
      pageInfo {
        hasNextPage
        startCursor
        endCursor
      }
      edges {
        node {
          id
          accounts {
            name
            buckets {
              bucketName
              allocatedAmount
            }
          }
          isCommitted
          initialBalance
          remainingBalance
        }
      }
    }
  }
`;
const { data, error, executeQuery } = useQuery({ query: GET_MONEY_PLANS });
watchEffect(() => {
  if (data.value) {
    moneyPlans.value = data.value.moneyPlans.edges.map((edge: { node: MoneyPlan }) => edge.node);
  }
  if (error.value) {
    console.error(error.value);
  }
});
onMounted(() => {
  executeQuery();
});
const addPlan = (newPlan: MoneyPlan) => {
  moneyPlans.value.push(newPlan);
};
</script>

<style scoped>
/* Add any scoped styles here */
</style>
