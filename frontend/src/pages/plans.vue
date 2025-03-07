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
          <button @click="filterStatus = 'all'" 
                  class="btn btn-sm" 
                  :class="filterStatus === 'all' ? 'btn-primary' : 'btn-outline'">
            All
          </button>
          <button @click="filterStatus = 'draft'" 
                  class="btn btn-sm" 
                  :class="filterStatus === 'draft' ? 'btn-primary' : 'btn-outline'">
            Drafts
          </button>
          <button @click="filterStatus = 'committed'" 
                  class="btn btn-sm" 
                  :class="filterStatus === 'committed' ? 'btn-primary' : 'btn-outline'">
            Committed
          </button>
        </div>
      </div>
      
      <!-- Plans List -->
      <div class="grid gap-4 md:gap-6 px-3">
        <!-- Empty state when no plans -->
        <div v-if="filteredPlans.length === 0" class="card bg-base-100 shadow-xl">
          <div class="card-body text-center py-6 md:py-10">
            <h2 class="card-title justify-center text-lg md:text-xl">No Money Plans Found</h2>
            <p class="text-sm md:text-base" v-if="filterStatus !== 'all'">
              No {{ filterStatus }} plans found. Try changing the filter or create a new plan.
            </p>
            <p class="text-sm md:text-base" v-else>
              You don't have any money plans yet. Click the "Start New Plan" button to create one.
            </p>
          </div>
        </div>
        
        <!-- Display filtered plans -->
        <MoneyPlanCard 
          v-for="plan in filteredPlans" 
          :key="plan.id" 
          :plan="plan" 
        />
      </div>
    </div>
    
    <StartPlanDialog v-if="showStartPlanDialog" @close="showStartPlanDialog = false" @planCreated="addPlan" />
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
  name: string;
  buckets: Bucket[];
}

interface MoneyPlan {
  id: string;
  timestamp: string;
  accounts: Account[];
  isCommitted: boolean;
  initialBalance: number;
  remainingBalance: number;
}

const showStartPlanDialog = ref(false);
const moneyPlans = ref<MoneyPlan[]>([]);
const filterStatus = ref('all'); // 'all', 'draft', or 'committed'

// Computed property to filter plans based on selected status
const filteredPlans = computed(() => {
  if (filterStatus.value === 'all') {
    return moneyPlans.value;
  } else if (filterStatus.value === 'draft') {
    return moneyPlans.value.filter(plan => !plan.isCommitted);
  } else {
    return moneyPlans.value.filter(plan => plan.isCommitted);
  }
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
          timestamp
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