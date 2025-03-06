<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900">
          Money Plans
        </h1>
      </div>
    </header>
    <main>
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
          <div class="border-4 border-dashed border-gray-200 rounded-lg h-96">
            <!-- Money Plans List -->
            <div class="p-4 bg-white rounded-lg shadow-md">
              <h2 class="text-2xl font-semibold mb-4">Your Money Plans</h2>
              <ul>
                <li v-for="plan in moneyPlans" :key="plan.id" class="mb-2">
                  <div class="p-4 bg-gray-100 rounded-md">
                    <h3 class="text-xl font-bold">Plan ID: {{ plan.id }}</h3>
                    <p>Initial Balance: {{ plan.initialBalance }}</p>
                    <p>Remaining Balance: {{ plan.remainingBalance }}</p>
                    <p>Is Committed: {{ plan.isCommitted }}</p>
                    <div v-for="account in plan.accounts" :key="account.name" class="mt-2">
                      <h4 class="text-lg font-semibold">Account: {{ account.name }}</h4>
                      <ul>
                        <li v-for="bucket in account.buckets" :key="bucket.bucketName" class="ml-4">
                          <p>Bucket Name: {{ bucket.bucketName }}</p>
                          <p>Allocated Amount: {{ bucket.allocatedAmount }}</p>
                        </li>
                      </ul>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
            <!-- Action Button -->
            <div class="mt-4">
              <button @click="showStartPlanDialog = true" class="px-4 py-2 bg-blue-500 text-white rounded-md">Start New Plan</button>
            </div>
          </div>
        </div>
      </div>
    </main>
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
