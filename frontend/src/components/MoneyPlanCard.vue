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
            :title="getArchiveTooltip()"
          >
            <i v-if="!isArchiving" class="fa-solid fa-box-archive"></i>
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

      <!-- Notes section with edit button -->
      <div class="flex justify-between items-start mb-4">
        <div class="flex-grow text-sm md:text-base text-base-content/80">
          <p v-if="plan.notes">{{ plan.notes }}</p>
          <p v-else class="text-base-content/50 italic">No notes for this plan</p>
        </div>
        <button 
          v-if="!plan.isArchived" 
          @click="showEditPlanNotes = true" 
          class="btn btn-ghost btn-sm btn-square"
          title="Edit plan notes"
        >
          <i class="fa-solid fa-file-lines text-info"></i>
        </button>
      </div>
      
      <div class="divider my-1 md:my-2">Accounts</div>
      
      <!-- Using the new AccountCard component for each account -->
      <AccountCard
        v-for="account in plan.accounts"
        :key="account.id"
        :account="account"
        :plan-initial-balance="plan.initialBalance"
        :is-archived="plan.isArchived"
        :is-committed="plan.isCommitted"
        @toggle-check="toggleAccountCheck"
        @edit-notes="editAccountNotes"
        @edit-account="$emit('edit-account', account)"
        @remove-account="$emit('remove-account', account)"
      />
    </div>
    
    <!-- Edit Plan Notes Modal -->
    <EditPlanNotesModal
      v-if="showEditPlanNotes"
      :plan-id="plan.id"
      :initial-notes="plan.notes"
      @close="showEditPlanNotes = false"
      @notes-saved="handlePlanNotesUpdated"
    />
    
    <!-- Edit Account Notes Modal -->
    <EditAccountNotesModal
      v-if="selectedAccount"
      :plan-id="plan.id"
      :account-id="selectedAccount.id"
      :account-name="selectedAccount.name"
      :initial-notes="selectedAccount.notes"
      @close="selectedAccount = null"
      @notes-saved="handleAccountNotesUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMutation } from '@urql/vue';
import PlanDate from './PlanDate.vue';
import EditPlanNotesModal from './EditPlanNotesModal.vue';
import EditAccountNotesModal from './EditAccountNotesModal.vue';
import AccountCard from './AccountCard.vue';

interface Bucket {
  bucketName: string;
  allocatedAmount: number;
  category?: string;
}

interface Account {
  id: string;
  name: string;
  buckets: Bucket[];
  isChecked: boolean;
  notes: string;
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

const props = defineProps<{
  plan: MoneyPlan
}>();

const emit = defineEmits([
  'planArchived', 
  'planUpdated', 
  'edit-account', 
  'remove-account'
]);

const isArchiving = ref(false);
const showEditPlanNotes = ref(false);
const selectedAccount = ref<Account | null>(null);

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
          }
        }
      }
    }
  }
`;

const { executeMutation } = useMutation(ARCHIVE_PLAN_MUTATION);
const { executeMutation: executeAccountCheckMutation } = useMutation(SET_ACCOUNT_CHECKED_MUTATION);

function getBadgeClass() {
  if (props.plan.isArchived) return 'badge-ghost';
  return props.plan.isCommitted ? '' : 'badge-ghost';
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

function getArchiveTooltip() {
  if (props.plan.isCommitted) {
    return "Archive this committed plan to hide it from the default view";
  }
  return "Archive this draft plan if you no longer need it";
}

function editAccountNotes(account: Account) {
  selectedAccount.value = account;
}

async function toggleAccountCheck(account: Account) {
  try {
    const result = await executeAccountCheckMutation({
      input: {
        planId: props.plan.id,
        accountId: account.id,
        isChecked: !account.isChecked
      }
    });

    if (result.error) {
      console.error('Error toggling account check state:', result.error);
      return;
    }
    if (result.data?.moneyPlan?.setAccountCheckedState?.success) {
      emit('planUpdated', result.data.moneyPlan.setAccountCheckedState.moneyPlan);
    } else {
      console.error('Failed to toggle account check state:', 
        result.data?.moneyPlan?.setAccountCheckedState?.error?.message);
    }
  } catch (e) {
    console.error('Error toggling account check state:', e);
  }
}

function handlePlanNotesUpdated(updatedPlan: MoneyPlan) {
  emit('planUpdated', updatedPlan);
}

function handleAccountNotesUpdated(updatedPlan: MoneyPlan) {
  emit('planUpdated', updatedPlan);
}
</script>