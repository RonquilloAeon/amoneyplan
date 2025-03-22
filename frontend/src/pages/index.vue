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
            
            <!-- Notes section with edit button -->
            <div class="flex justify-between items-start mb-4">
              <div class="flex-grow text-sm md:text-base text-base-content/80">
                <p v-if="draftPlan.notes">{{ draftPlan.notes }}</p>
                <p v-else class="text-base-content/50 italic">No notes for this plan</p>
              </div>
              <button 
                @click="showEditPlanNotes = true" 
                class="btn btn-ghost btn-sm btn-square"
                title="Edit plan notes"
              >
                <i class="fa-solid fa-file-lines text-secondary"></i>
              </button>
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
            
            <!-- Accounts list using the new AccountCard component -->
            <div v-else>
              <AccountCard
                v-for="account in draftPlan.accounts" 
                :key="account.id"
                :account="account"
                :plan-initial-balance="draftPlan.initialBalance"
                :is-archived="draftPlan.isArchived"
                :is-committed="draftPlan.isCommitted"
                @toggle-check="toggleAccountCheck"
                @edit-notes="editAccountNotes"
                @edit-account="editAccount"
                @remove-account="confirmRemoveAccount"
              />
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
      v-if="draftPlan" 
      :planId="draftPlan.id"
      :currentRemainingBalance="draftPlan.remainingBalance"
      :isOpen="showAddAccountModal"
      @close="showAddAccountModal = false" 
      @accountAdded="handleAccountAdded" 
    />
    
    <!-- Edit Account Modal -->
    <EditAccountModal
      v-if="draftPlan && accountToEdit"
      :planId="draftPlan.id"
      :accountId="accountToEdit.id"
      :accountName="accountToEdit.name"
      :originalBuckets="accountToEdit.buckets"
      :currentAccountTotal="calculateAccountTotal(accountToEdit)"
      :currentRemainingBalance="draftPlan.remainingBalance"
      :isOpen="showEditAccountModal"
      @close="closeEditModal"
      @accountUpdated="handleAccountAdded"
    />
    
    <!-- Edit Plan Notes Modal -->
    <EditPlanNotesModal
      v-if="showEditPlanNotes && draftPlan"
      :plan-id="draftPlan.id"
      :initial-notes="draftPlan.notes"
      @close="showEditPlanNotes = false"
      @notes-saved="handlePlanNotesUpdated"
    />
    
    <!-- Edit Account Notes Modal -->
    <EditAccountNotesModal
      v-if="accountForNotes && draftPlan"
      :plan-id="draftPlan.id"
      :account-id="accountForNotes.id"
      :account-name="accountForNotes.name"
      :initial-notes="accountForNotes.notes"
      @close="accountForNotes = null"
      @notes-saved="handleAccountNotesUpdated"
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
import EditAccountModal from '../components/EditAccountModal.vue';
import EditPlanNotesModal from '../components/EditPlanNotesModal.vue';
import EditAccountNotesModal from '../components/EditAccountNotesModal.vue';
import PageHeader from '../components/PageHeader.vue';
import PlanDate from '../components/PlanDate.vue';
import AccountCard from '../components/AccountCard.vue';

interface Bucket {
  bucketName: string;
  allocatedAmount: number;
  category: string;
}

interface Account {
  id: string;
  name: string;
  buckets: Bucket[];
  notes: string;
  isChecked: boolean;
}

interface MoneyPlan {
  id: string;
  timestamp: string;
  accounts: Account[];
  isCommitted: boolean;
  isArchived: boolean;
  initialBalance: number;
  remainingBalance: number;
  notes: string;
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

const REMOVE_ACCOUNT_MUTATION = `
  mutation removeAccount($input: RemoveAccountInput!) {
    moneyPlan {
      removeAccount(input: $input) {
        error {
          message
        }
        success
        moneyPlan {
          id
          accounts {
            id
            name
            notes
            isChecked
            buckets {
              bucketName
              allocatedAmount
              category
            }
          }
          initialBalance
          remainingBalance
          timestamp
          notes
        }
      }
    }
  }
`;

const SET_ACCOUNT_CHECKED_MUTATION = `
  mutation setAccountCheckedState($input: SetAccountCheckedStateInput!) {
    moneyPlan {
      setAccountCheckedState(input: $input) {
        success
        error {
          message
        }
        moneyPlan {
          id
          accounts {
            id
            name
            isChecked
            notes
            buckets {
              bucketName
              allocatedAmount
              category
            }
          }
          initialBalance
          remainingBalance
          timestamp
          notes
        }
      }
    }
  }
`;

const showStartPlanDialog = ref(false);
const showAddAccountModal = ref(false);
const showEditAccountModal = ref(false);
const showEditPlanNotes = ref(false);
const accountToEdit = ref<Account | null>(null);
const accountForNotes = ref<Account | null>(null);
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
  return moneyPlans.value.find(plan => !plan.isCommitted && !plan.isArchived);
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
            id
            name
            notes
            isChecked
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
          notes
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
      isArchived: false // Only show non-archived plans
    }
  },
  requestPolicy: 'cache-and-network'
});

const { executeMutation: executeCommitPlan } = useMutation(COMMIT_PLAN);
const { executeMutation: executeArchivePlan } = useMutation(ARCHIVE_PLAN);
const { executeMutation: executeRemoveAccount } = useMutation(REMOVE_ACCOUNT_MUTATION);
const { executeMutation: executeAccountCheckMutation } = useMutation(SET_ACCOUNT_CHECKED_MUTATION);

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

const addPlan = (_newPlan: MoneyPlan) => {
  // Show success message
  showToast('Plan created successfully!', 'alert-success');
  // Force refresh from network to get the new plan
  executeQuery({ requestPolicy: 'network-only' });
};

function handleAccountAdded(updatedPlan: MoneyPlan) {
  // Find and update the plan in our list
  const index = moneyPlans.value.findIndex(plan => plan.id === updatedPlan.id);
  if (index !== -1) {
    moneyPlans.value[index] = updatedPlan;
  }
  showToast('Account updated successfully', 'alert-success');
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
      // Clear the plans list since archived plan is no longer a draft
      moneyPlans.value = [];
      // Refresh the query to make sure we get any other draft plans
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

function editAccount(account: Account) {
  accountToEdit.value = account;
  showEditAccountModal.value = true;
}

function closeEditModal() {
  showEditAccountModal.value = false;
  accountToEdit.value = null;
}

async function confirmRemoveAccount(account: Account) {
  const confirmed = window.confirm(`Are you sure you want to remove the account "${account.name}"? All buckets and allocations will be returned to the remaining balance.`);
  if (!confirmed) return;
  
  try {
    const result = await executeRemoveAccount({
      input: {
        planId: draftPlan.value.id,
        accountId: account.id,
      }
    });
    
    if (result.error) {
      showToast(result.error.message, 'alert-error');
      return;
    }
    
    if (result.data?.moneyPlan?.removeAccount?.error) {
      showToast(result.data.moneyPlan.removeAccount.error.message, 'alert-error');
      return;
    }
    
    if (result.data?.moneyPlan?.removeAccount?.success) {
      const updatedPlan = result.data.moneyPlan.removeAccount.moneyPlan;
      handleAccountAdded(updatedPlan); // Reuse existing function to update the plan
      showToast(`Account "${account.name}" removed successfully`, 'alert-success');
    }
  } catch (error) {
    showToast((error as Error).message, 'alert-error');
  }
}

function editAccountNotes(account: Account) {
  accountForNotes.value = account;
}

async function toggleAccountCheck(account: Account) {
  try {
    const result = await executeAccountCheckMutation({
      input: {
        planId: draftPlan.value.id,
        accountId: account.id,
        isChecked: !account.isChecked
      }
    });

    if (result.error) {
      console.error('Error toggling account check state:', result.error);
      showToast('Failed to update account status', 'alert-error');
      return;
    }
    
    if (result.data?.moneyPlan?.setAccountCheckedState?.success) {
      const updatedPlan = result.data.moneyPlan.setAccountCheckedState.moneyPlan;
      handleAccountAdded(updatedPlan);
      
      // Show a toast based on the new state
      const message = account.isChecked ? 
        `Unchecked account: ${account.name}` : 
        `Checked account: ${account.name}`;
      showToast(message, 'alert-success');
    } else {
      const errorMessage = result.data?.moneyPlan?.setAccountCheckedState?.error?.message || 
        'Failed to update account status';
      showToast(errorMessage, 'alert-error');
    }
  } catch (e) {
    console.error('Error toggling account check state:', e);
    showToast('An error occurred while updating the account', 'alert-error');
  }
}

function handlePlanNotesUpdated(updatedPlan: MoneyPlan) {
  // Find and update the plan in our list
  const index = moneyPlans.value.findIndex(plan => plan.id === updatedPlan.id);
  if (index !== -1) {
    moneyPlans.value[index] = {
      ...moneyPlans.value[index],
      notes: updatedPlan.notes
    };
  }
  showToast('Plan notes updated successfully', 'alert-success');
}

function handleAccountNotesUpdated(updatedPlan: MoneyPlan) {
  // Find and update the plan in our list
  const index = moneyPlans.value.findIndex(plan => plan.id === updatedPlan.id);
  if (index !== -1) {
    // Preserve the timestamp and merge the updated plan data
    const existingTimestamp = moneyPlans.value[index].timestamp;
    moneyPlans.value[index] = {
      ...updatedPlan,
      timestamp: existingTimestamp || updatedPlan.timestamp
    };
  }
  showToast('Account notes updated successfully', 'alert-success');
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
