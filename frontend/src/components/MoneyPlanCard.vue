<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body p-4 md:p-6">
      <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
        <h2 class="card-title text-base md:text-lg">
          <PlanDate :planDate="plan.planDate" />
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
        v-for="planAccount in plan.planAccounts"
        :key="planAccount.id"
        :account="planAccount.account"
        :buckets="planAccount.buckets"
        :is-checked="planAccount.isChecked"
        :plan-initial-balance="plan.initialBalance"
        :is-archived="plan.isArchived"
        :is-committed="plan.isCommitted"
        @toggle-check="toggleAccountCheck"
        @edit-notes="editAccountNotes"
        @edit-account="$emit('edit-account', planAccount)"
        @remove-account="$emit('remove-account', planAccount)"
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
      :account-id="selectedAccount.account.id"
      :account-name="selectedAccount.account.name"
      :initial-notes="selectedAccount.account.notes"
      @close="selectedAccount = null"
      @notes-saved="handleAccountNotesUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMutation } from '@urql/vue';
import { getClient } from '../graphql/moneyPlans';
import PlanDate from './PlanDate.vue';
import EditPlanNotesModal from './EditPlanNotesModal.vue';
import EditAccountNotesModal from './EditAccountNotesModal.vue';
import AccountCard from './AccountCard.vue';

interface Bucket {
  id: string;
  name: string;
  allocatedAmount: number;
  category: string;
}

interface Account {
  id: string;
  name: string;
  type: string;
  notes?: string;
}

interface PlanAccount {
  id: string;
  account: Account;
  buckets: Bucket[];
  isChecked: boolean;
}

interface MoneyPlan {
  id: string;
  planDate: string;
  planAccounts: PlanAccount[];
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
const selectedAccount = ref<PlanAccount | null>(null);

const ARCHIVE_PLAN_MUTATION = gql`
  mutation archivePlan($input: ArchivePlanInput!) {
    moneyPlan {
      archivePlan(input: $input) {
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

const SET_ACCOUNT_CHECKED_MUTATION = gql`
  mutation setAccountCheckedState($input: SetAccountCheckedStateInput!) {
    moneyPlan {
      setAccountCheckedState(input: $input) {
        error {
          message
        }
        moneyPlan {
          id
          planAccounts {
            id
            isChecked
          }
        }
      }
    }
  }
`;

const { executeMutation } = useMutation(ARCHIVE_PLAN_MUTATION, {
  client: () => getClient()
});
const { executeMutation: executeAccountCheckMutation } = useMutation(SET_ACCOUNT_CHECKED_MUTATION, {
  client: () => getClient()
});

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
    if (result.data?.moneyPlan?.archivePlan?.error) {
      console.error('Failed to archive plan:', result.data.moneyPlan.archivePlan.error.message);
      return;
    }
    emit('planArchived', result.data.moneyPlan.archivePlan.moneyPlan);
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

function editAccountNotes(planAccount: PlanAccount) {
  selectedAccount.value = planAccount;
}

async function toggleAccountCheck(planAccount: PlanAccount) {
  try {
    const result = await executeAccountCheckMutation({
      input: {
        planId: props.plan.id,
        planAccountId: planAccount.id,
        isChecked: !planAccount.isChecked
      }
    });

    if (result.error) {
      console.error('Error toggling account check state:', result.error);
      return;
    }
    if (result.data?.moneyPlan?.setAccountCheckedState?.error) {
      console.error('Failed to toggle account check state:', 
        result.data.moneyPlan.setAccountCheckedState.error.message);
      return;
    }
    emit('planUpdated', result.data.moneyPlan.setAccountCheckedState.moneyPlan);
  } catch (e) {
    console.error('Error toggling account check state:', e);
  }
}

function handlePlanNotesUpdated(updatedPlan: MoneyPlan) {
  emit('planUpdated', updatedPlan);
}

function handleAccountNotesUpdated(updatedPlan: MoneyPlan) {
  emit('planUpdated', updatedPlan);
  selectedAccount.value = null;
}
</script>