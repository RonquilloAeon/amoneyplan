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

        <div class="form-control w-full mb-3 md:mb-4">
          <label class="label py-1">
            <span class="label-text text-sm md:text-base">Plan Date</span>
          </label>
          <input 
            v-model="planDate" 
            type="date" 
            class="input input-bordered input-sm md:input-md w-full" 
            required 
          />
        </div>
        
        <div class="form-control w-full mb-3 md:mb-4">
          <label class="label py-1">
            <span class="label-text text-sm md:text-base">Copy from previous plan (optional)</span>
          </label>
          <CopyFromSelect v-model="selectedPlanId" />
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
import { ref, onMounted } from 'vue';
import { CREATE_MONEY_PLAN, DRAFT_MONEY_PLAN_QUERY, getClient } from '../graphql/moneyPlans';
import CopyFromSelect from './CopyFromSelect.vue';

const emit = defineEmits(['close', 'planCreated']);

const initialBalance = ref(0);
const notes = ref('');
const selectedPlanId = ref('');
const planDate = ref(new Date().toISOString().split('T')[0]); // Default to today's date

const startPlan = async () => {
  const variables = { 
    input: { 
      initialBalance: initialBalance.value, 
      notes: notes.value,
      copyFrom: selectedPlanId.value ? selectedPlanId.value : null,
      planDate: planDate.value
    } 
  };
  
  const client = getClient();
  const response = await client.mutation(CREATE_MONEY_PLAN, variables).toPromise();
  
  if (!response.error) {
    const result = response.data?.moneyPlan?.startPlan;
    if (result?.__typename === 'Success') {
      // Fetch the draft plan to get the full data
      const draftClient = getClient(); // Get a fresh client instance
      const draftResponse = await draftClient.query(DRAFT_MONEY_PLAN_QUERY).toPromise();
      if (!draftResponse.error && draftResponse.data?.draftMoneyPlan) {
        // Emit the new plan to the parent component
        emit('planCreated', draftResponse.data.draftMoneyPlan);
        emit('close');
      } else {
        console.error('Failed to fetch draft plan:', draftResponse.error);
      }
    } else {
      console.error('Failed to create plan:', result?.message);
    }
  } else {
    console.error(response.error);
  }
};

// Reset form when modal opens
onMounted(() => {
  initialBalance.value = 0;
  notes.value = '';
  selectedPlanId.value = '';
  planDate.value = new Date().toISOString().split('T')[0];
});
</script>

<style scoped>
/* Add any scoped styles here */
</style>
