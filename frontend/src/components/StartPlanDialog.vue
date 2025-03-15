<template>
  <dialog id="start-plan-modal" class="modal modal-open">
    <div class="modal-box relative w-11/12 max-w-sm md:max-w-md">
      <h3 class="font-bold text-base md:text-lg mb-3 md:mb-4">Start New Plan</h3>
      
      <form @submit.prevent="startPlan">
        <div class="form-control w-full mb-3 md:mb-4">
          <label class="label py-1">
            <span class="label-text text-sm md:text-base">Initial Balance</span>
          </label>
          <input 
            v-model="initialBalance" 
            type="number" 
            step="0.01"
            min="1.00"
            class="input input-bordered input-sm md:input-md w-full" 
            required 
          />
        </div>
        
        <div class="form-control w-full mb-4 md:mb-6">
          <label class="label py-1">
            <span class="label-text text-sm md:text-base">Notes (optional)</span>
          </label>
          <textarea 
            v-model="notes" 
            class="textarea textarea-bordered textarea-sm md:textarea-md h-16 md:h-24 text-sm md:text-base"
          ></textarea>
        </div>
        
        <div class="modal-action">
          <button type="button" @click="$emit('close')" class="btn btn-ghost btn-sm md:btn-md">Cancel</button>
          <button type="submit" class="btn btn-primary btn-sm md:btn-md">Start Plan</button>
        </div>
      </form>
      <form method="dialog">
        <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2" @click="$emit('close')">✕</button>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="$emit('close')">close</button>
    </form>
  </dialog>
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
        success
        moneyPlan {
          id
          timestamp
          notes
          accounts {
            name
            buckets {
              bucketName
              allocatedAmount
            }
          }
          isCommitted
          isArchived
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
