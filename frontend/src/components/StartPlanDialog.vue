<template>
  <div class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-1/3">
      <h2 class="text-2xl font-semibold mb-4">Start New Plan</h2>
      <form @submit.prevent="startPlan">
        <div class="mb-4">
          <label for="initialBalance" class="block text-sm font-medium text-gray-700">Initial Balance</label>
          <input v-model="initialBalance" type="number" id="initialBalance" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required />
        </div>
        <div class="mb-4">
          <label for="notes" class="block text-sm font-medium text-gray-700">Notes</label>
          <textarea v-model="notes" id="notes" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required></textarea>
        </div>
        <div class="flex justify-end">
          <button type="button" @click="$emit('close')" class="px-4 py-2 bg-gray-500 text-white rounded-md mr-2">Cancel</button>
          <button type="submit" class="px-4 py-2 bg-blue-500 text-white rounded-md">Start Plan</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue';
import { useMutation } from '@urql/vue';
import gql from 'graphql-tag';

const emit = defineEmits(['close', 'planCreated']);

const START_PLAN_MUTATION = gql`
  mutation StartPlan($input: PlanStartInput!) {
    moneyPlan {
      startPlan(input: $input) {
        error {
          message
        }
        moneyPlan {
          id
          initialBalance
          remainingBalance
        }
      }
    }
  }
`;

const initialBalance = ref(0);
const notes = ref('');
const { executeMutation } = useMutation(START_PLAN_MUTATION);

const startPlan = async () => {
  const variables = { input: { initialBalance: initialBalance.value, notes: notes.value } };
  const response = await executeMutation(variables);
  if (!response.error) {
    // Emit the new plan to the parent component
    emit('planCreated', response.data.moneyPlan.startPlan.moneyPlan);
    emit('close');
  } else {
    console.error(response.error);
  }
};
</script>

<style scoped>
/* Add any scoped styles here */
</style>
