<template>
  <div class="min-h-screen bg-base-200">
    <!-- Hero section with title -->
    <PageHeader 
      title="Money Plans"
      subtitle="Manage your finances with smart money plans"
      :centered="true"
    />

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
        <!-- Show draft plan if exists -->
        <div v-if="draftPlan" class="card bg-base-100 shadow-xl">
          <div class="card-body p-4 md:p-6">
            <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
              <h2 class="card-title text-base md:text-lg">Plan ID: {{ draftPlan.id }}</h2>
              <div class="badge badge-md md:badge-lg badge-ghost">
                Draft
              </div>
            </div>
            
            <div class="stats shadow my-2 md:my-4 stats-vertical md:stats-horizontal">
              <div class="stat p-2 md:p-4">
                <div class="stat-title text-xs md:text-sm">Initial Balance</div>
                <div class="stat-value text-primary text-lg md:text-2xl">${{ draftPlan.initialBalance }}</div>
              </div>
              
              <div class="stat p-2 md:p-4">
                <div class="stat-title text-xs md:text-sm">Remaining Balance</div>
                <div class="stat-value text-lg md:text-2xl" :class="draftPlan.remainingBalance > 0 ? 'text-success' : 'text-error'">
                  ${{ draftPlan.remainingBalance }}
                </div>
              </div>
            </div>

            <!-- Add Account button -->
            <div v-if="draftPlan.remainingBalance > 0" class="flex justify-end mb-4">
              <button @click="showAddAccountModal = true" class="btn btn-sm btn-outline">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 mr-1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add Account
              </button>
            </div>
            
            <div class="divider my-1 md:my-2">Accounts</div>
            
            <!-- No accounts message -->
            <div v-if="!draftPlan.accounts || draftPlan.accounts.length === 0" class="text-center py-6">
              <p class="text-sm md:text-base text-gray-500">No accounts added yet</p>
              <button 
                v-if="draftPlan.remainingBalance > 0"
                @click="showAddAccountModal = true" 
                class="btn btn-sm btn-outline mt-2"
              >
                Add your first account
              </button>
            </div>
            
            <div v-else v-for="account in draftPlan.accounts" :key="account.name" class="mb-2 md:mb-4">
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
                          <th>Category</th>
                          <th>Allocated Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="bucket in account.buckets" :key="bucket.bucketName">
                          <td>{{ bucket.bucketName }}</td>
                          <td>{{ bucket.category || 'N/A' }}</td>
                          <td>${{ bucket.allocatedAmount }}</td>
                        </tr>
                        <!-- Account total row -->
                        <tr class="font-semibold border-t">
                          <td colspan="2" class="text-right">Account Total:</td>
                          <td>${{ calculateAccountTotal(account) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Empty state when no draft plans -->
        <div v-if="!draftPlan" class="card bg-base-100 shadow-xl">
          <div class="card-body text-center py-6 md:py-10">
            <h2 class="card-title justify-center text-lg md:text-xl">No Draft Plans</h2>
            <p class="text-sm md:text-base">Click the "Start New Plan" button to create a new plan.</p>
            <div class="mt-4">
              <RouterLink to="/plans" class="btn btn-outline btn-sm md:btn-md">
                View All Plans
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <StartPlanDialog v-if="showStartPlanDialog" @close="showStartPlanDialog = false" @planCreated="addPlan" />
    
    <!-- Add Account Modal -->
    <AddAccountModal 
      v-if="showAddAccountModal && draftPlan" 
      :planId="draftPlan.id"
      :currentRemainingBalance="draftPlan.remainingBalance"
      @close="showAddAccountModal = false" 
      @accountAdded="handleAccountAdded" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watchEffect } from 'vue';
import { useQuery } from '@urql/vue';
import { RouterLink } from 'vue-router';
import StartPlanDialog from '../components/StartPlanDialog.vue';
import AddAccountModal from '../components/AddAccountModal.vue';
import PageHeader from '../components/PageHeader.vue';

interface Bucket {
  bucketName: string;
  allocatedAmount: number;
  category: string;
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
const showAddAccountModal = ref(false);
const moneyPlans = ref<MoneyPlan[]>([]);

// Computed property to get the first draft plan (if any)
const draftPlan = computed(() => {
  return moneyPlans.value.find(plan => !plan.isCommitted);
});

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
              category
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

function handleAccountAdded(updatedPlan: MoneyPlan) {
  // Find and update the plan in our list
  const index = moneyPlans.value.findIndex(plan => plan.id === updatedPlan.id);
  if (index !== -1) {
    moneyPlans.value[index] = updatedPlan;
  }
}

// Calculate the total amount allocated for an account
function calculateAccountTotal(account: Account): number {
  return account.buckets.reduce((total, bucket) => total + bucket.allocatedAmount, 0);
}
</script>

<style scoped>
/* Add any scoped styles here */
</style>
