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
  bucketName: string;
  allocatedAmount: number;
}

interface Account {
  id: string;
  name: string;
  notes: string;
  isChecked: boolean;
  buckets: Bucket[];
}

interface MoneyPlan {
  id: string;
  planDate: string;
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

const showStartPlanDialog = ref(false);
const moneyPlans = ref<MoneyPlan[]>([]);
const filterStatus = ref('active'); // 'active' or 'archived'
const toast = ref<Toast>({
  show: false,
  message: '',
  type: 'alert-info'
});

// Create a computed property for the filter
const currentFilter = computed(() => ({
  isArchived: filterStatus.value === 'archived',
  status: null // We don't filter by draft/committed status anymore
}));

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
          planDate
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
          notes
        }
      }
    }
  }
`;

const { data, error, executeQuery } = useQuery({
  query: GET_MONEY_PLANS,
  variables: { filter: currentFilter },
  requestPolicy: 'cache-and-network' // This will ensure we get fresh data while showing cached data
});

// Watch for filter changes and rerun the query
watchEffect(() => {
  executeQuery({ filter: currentFilter.value });
});

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
  executeQuery({ filter: currentFilter.value });
});

const addPlan = () => {
  // Show success message
  showToast('Plan created successfully', 'alert-success');
  // Force a refresh of the data
  executeQuery({ 
    filter: currentFilter.value,
    requestPolicy: 'network-only' // Force fresh data from server
  });
};

function handlePlanArchived(_updatedPlan: MoneyPlan) {
  // Show success message
  showToast('Plan archived successfully', 'alert-success');
  
  // Refresh the plans list
  executeQuery({ filter: currentFilter.value });
}

function handlePlanUpdated(_updatedPlan: MoneyPlan) {
  // Show success message
  showToast('Plan updated successfully', 'alert-success');
  
  // Refresh the plans list to get the latest data
  executeQuery({ 
    filter: currentFilter.value,
    requestPolicy: 'network-only' // Force fresh data from server
  });
}

function handleEditAccount(account: Account) {
  // In the plans view, we can't edit accounts, but we can handle the event
  showToast(`Cannot edit account "${account.name}" in this view`, 'alert-info');
}

function handleRemoveAccount(account: Account) {
  // In the plans view, we can't remove accounts, but we can handle the event
  showToast(`Cannot remove account "${account.name}" in this view`, 'alert-info');
}

function showToast(message: string, type: string = 'alert-info', duration: number = 3000) {
  toast.value = {
    show: true,
    message,
    type
  };
  setTimeout(() => {
    toast.value.show = false;
  }, duration);
}
</script>

<style scoped>
/* Add any scoped styles here */
</style>