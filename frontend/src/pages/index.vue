<template>
  <div class="min-h-screen bg-base-200">
    <!-- Hero section with title -->
    <PageHeader 
      title="Money planning made simple"
      subtitle="Manage your finances with smart money plans"
      :centered="true"
    />

    <div class="container mx-auto pb-8">
      <!-- Action Button with responsive positioning -->
      <div class="flex justify-center sm:justify-end mb-4 px-4">
        <button 
          @click="showStartPlanDialog = true" 
          class="btn btn-primary btn-sm md:btn-md"
          :disabled="!!draftPlan"
          :class="{'btn-disabled': !!draftPlan}"
          :title="draftPlan ? 'Complete your draft plan first' : 'Start a new plan'"
        >
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
              <h2 class="card-title text-base md:text-lg">
                <PlanDate :timestamp="draftPlan.timestamp" />
              </h2>
              <div class="flex gap-2 items-center">
                <div class="badge badge-md md:badge-lg badge-ghost">
                  Draft
                </div>
                <button 
                  @click="archivePlan"
                  class="btn btn-sm btn-square btn-ghost"
                  :class="{'loading': isArchivingPlan}"
                  :disabled="isArchivingPlan"
                  title="Archive this draft plan if you no longer need it"
                >
                  <svg v-if="!isArchivingPlan" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m8.25 3v6.75m0-6.75h-3m3 0h3M12 3v1.5m-2.25 0h4.5" />
                  </svg>
                </button>
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
            
            <!-- Commit Plan section at the bottom of draft plan -->
            <div class="mt-4 flex flex-col items-center">
              <button 
                @click="commitPlan"
                class="btn btn-primary"
                :disabled="draftPlan.remainingBalance !== 0"
                :class="{'btn-disabled': draftPlan.remainingBalance !== 0, 'loading': isCommittingPlan}"
              >
                <span v-if="!isCommittingPlan">Commit Plan</span>
                <span v-else>Committing...</span>
              </button>
              <p v-if="draftPlan.remainingBalance !== 0" class="text-error mt-2 text-sm">
                You need to allocate all funds before committing the plan (Remaining: ${{ draftPlan.remainingBalance }})
              </p>
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

    <!-- Toast notifications -->
    <div class="toast toast-end" v-if="toast.show">
      <div class="alert" :class="toast.type">
        <span>{{ toast.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watchEffect } from 'vue';
import { useQuery, useMutation } from '@urql/vue';
import { RouterLink } from 'vue-router';
import StartPlanDialog from '../components/StartPlanDialog.vue';
import AddAccountModal from '../components/AddAccountModal.vue';
import PageHeader from '../components/PageHeader.vue';
import PlanDate from '../components/PlanDate.vue';

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
  timestamp: string;
  accounts: Account[];
  isCommitted: boolean;
  isArchived: boolean;
  initialBalance: number;
  remainingBalance: number;
}

interface Toast {
  show: boolean;
  message: string;
  type: string;
}

const ARCHIVE_PLAN = `
  mutation archivePlan($input: ArchivePlanInput!) {
    moneyPlan {
      archivePlan(input: $input) {
        error {
          message
        }
        success
        moneyPlan {
          isArchived
        }
      }
    }
  }
`;

const showStartPlanDialog = ref(false);
const showAddAccountModal = ref(false);
const moneyPlans = ref<MoneyPlan[]>([]);
const isCommittingPlan = ref(false);
const isArchivingPlan = ref(false);
const toast = ref<Toast>({
  show: false,
  message: '',
  type: 'alert-info'
});

// Computed property to get the first draft plan (if any)
const draftPlan = computed(() => {
  return moneyPlans.value.find(plan => !plan.isCommitted);
});

const GET_MONEY_PLANS = `
  query moneyPlans($filter: MoneyPlanFilter) {
    moneyPlans(filter: $filter) {
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
          isArchived
          initialBalance
          remainingBalance
          timestamp
        }
      }
    }
  }
`;

const COMMIT_PLAN = `
  mutation commitPlan($input: CommitPlanInput!) {
    moneyPlan {
      commitPlan(input: $input) {
        error {
          message
        }
        success
        moneyPlan {
          isCommitted
        }
      }
    }
  }
`;

const { data, error, executeQuery } = useQuery({
  query: GET_MONEY_PLANS,
  variables: { 
    filter: {
      status: 'draft'  // Only show draft plans on the home page
    }
  }
});

const { executeMutation: executeCommitPlan } = useMutation(COMMIT_PLAN);
const { executeMutation: executeArchivePlan } = useMutation(ARCHIVE_PLAN);

watchEffect(() => {
  if (data.value) {
    moneyPlans.value = data.value.moneyPlans.edges.map((edge: { node: MoneyPlan }) => edge.node);
  }
  if (error.value) {
    console.error(error.value);
    showToast('Failed to load money plans', 'alert-error');
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

// Show toast notification
function showToast(message: string, type: string = 'alert-info') {
  toast.value = {
    show: true,
    message,
    type
  };
  
  // Automatically hide the toast after 3 seconds
  setTimeout(() => {
    toast.value.show = false;
  }, 3000);
}

// Commit the current draft plan
async function commitPlan() {
  if (!draftPlan.value || draftPlan.value.remainingBalance !== 0) {
    return;
  }
  
  isCommittingPlan.value = true;
  
  try {
    const result = await executeCommitPlan({
      input: {
        planId: draftPlan.value.id
      }
    });
    
    if (result.data?.moneyPlan?.commitPlan?.success) {
      showToast('Plan committed successfully!', 'alert-success');
      // Refresh the plans list
      executeQuery();
    } else {
      const errorMessage = result.data?.moneyPlan?.commitPlan?.error?.message || 'Failed to commit plan';
      showToast(errorMessage, 'alert-error');
    }
  } catch (e) {
    console.error('Error committing plan:', e);
    showToast('An error occurred while committing the plan', 'alert-error');
  } finally {
    isCommittingPlan.value = false;
  }
}

// Archive the current draft plan
async function archivePlan() {
  if (!draftPlan.value || isArchivingPlan.value) return;
  
  isArchivingPlan.value = true;
  try {
    const result = await executeArchivePlan({
      input: {
        planId: draftPlan.value.id
      }
    });

    if (result.data?.moneyPlan?.archivePlan?.success) {
      showToast('Plan archived successfully', 'alert-success');
      // Refresh the plans list to remove the archived draft
      executeQuery();
    } else {
      const errorMessage = result.data?.moneyPlan?.archivePlan?.error?.message || 'Failed to archive plan';
      showToast(errorMessage, 'alert-error');
    }
  } catch (e) {
    console.error('Error archiving plan:', e);
    showToast('An error occurred while archiving the plan', 'alert-error');
  } finally {
    isArchivingPlan.value = false;
  }
}
</script>

<style scoped>
/* Add any scoped styles here */
.toast {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  z-index: 1000;
}
</style>
