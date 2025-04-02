<template>
  <div class="min-h-screen bg-base-200">
    <!-- Page Header -->
    <PageHeader 
      title="Your money plans"
      subtitle="View and manage all your money plans"
      :centered="true"
    />

    <div class="container mx-auto pb-8">
      <!-- Filter/Sort Controls -->
      <div class="flex flex-col sm:flex-row justify-between items-center gap-3 mb-6 px-4">
        <div class="flex gap-2">
          <button @click="filterStatus = 'active'" 
                  class="btn btn-sm" 
                  :class="filterStatus === 'active' ? 'btn-primary' : 'btn-outline'">
            Active
          </button>
          <button @click="filterStatus = 'archived'" 
                  class="btn btn-sm" 
                  :class="filterStatus === 'archived' ? 'btn-primary' : 'btn-outline'">
            Archived
          </button>
        </div>
      </div>
      
      <!-- Plans List -->
      <div class="grid gap-4 md:gap-6 px-3">
        <!-- Empty state when no plans -->
        <div v-if="moneyPlans.length === 0" class="card bg-base-100 shadow-xl">
          <div class="card-body text-center py-6 md:py-10">
            <h2 class="card-title justify-center text-lg md:text-xl">No Money Plans Found</h2>
            <p class="text-sm md:text-base" v-if="filterStatus !== 'active'">
              No {{ filterStatus }} plans found. Try changing the filter or create a new plan.
            </p>
            <p class="text-sm md:text-base" v-else>
              You don't have any money plans yet. Click the "Start New Plan" button to create one.
            </p>
          </div>
        </div>
        
        <!-- Display plans -->
        <MoneyPlanCard 
          v-for="plan in moneyPlans" 
          :key="plan.id" 
          :plan="plan" 
          @plan-archived="handlePlanArchived"
          @plan-updated="handlePlanUpdated"
          @edit-account="handleEditAccount"
          @remove-account="handleRemoveAccount"
        />
      </div>
    </div>
    
    <StartPlanDialog v-if="showStartPlanDialog" @close="showStartPlanDialog = false" @planCreated="addPlan" />
    
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
import { useQuery } from '@urql/vue';
import StartPlanDialog from '../components/StartPlanDialog.vue';
import MoneyPlanCard from '../components/MoneyPlanCard.vue';
import PageHeader from '../components/PageHeader.vue';

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

interface Toast {
  show: boolean;
  message: string;
  type: string;
}

const filterStatus = ref<'active' | 'archived'>('active');
const showStartPlanDialog = ref(false);
const toast = ref<Toast>({
  show: false,
  message: '',
  type: 'alert-success'
});

const MONEY_PLANS_QUERY = `
  query MoneyPlans {
    moneyPlans {
      id
      planDate
      planAccounts {
        id
        account {
          id
          name
          type
          notes
        }
        buckets {
          id
          name
          category
          allocatedAmount
        }
        isChecked
      }
      isCommitted
      isArchived
      initialBalance
      remainingBalance
      notes
    }
  }
`;

const { data, error } = useQuery({
  query: MONEY_PLANS_QUERY,
});

const moneyPlans = computed(() => {
  if (!data.value?.moneyPlans) return [];
  return data.value.moneyPlans.filter((plan: MoneyPlan) => 
    filterStatus.value === 'active' ? !plan.isArchived : plan.isArchived
  );
});

function showToast(message: string, type: string = 'alert-success') {
  toast.value = { show: true, message, type };
  setTimeout(() => {
    toast.value.show = false;
  }, 3000);
}

function handlePlanArchived(archivedPlan: MoneyPlan) {
  showToast('Plan archived successfully');
}

function handlePlanUpdated(updatedPlan: MoneyPlan) {
  showToast('Plan updated successfully');
}

function handleEditAccount(planAccount: PlanAccount) {
  // TODO: Implement account editing
}

function handleRemoveAccount(planAccount: PlanAccount) {
  // TODO: Implement account removal
}

function addPlan(newPlan: MoneyPlan) {
  showToast('New plan created successfully');
}
</script>

<style scoped>
/* Add any scoped styles here */
</style>