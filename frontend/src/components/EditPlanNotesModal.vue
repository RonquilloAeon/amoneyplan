<template>
  <div class="modal modal-open">
    <div class="modal-box">
      <h3 class="font-bold text-lg">Edit Plan Notes</h3>
      <div class="form-control w-full mt-4">
        <textarea
          class="textarea textarea-bordered h-32"
          placeholder="Enter your notes for this plan"
          v-model="noteText"
        ></textarea>
      </div>
      <div class="modal-action">
        <button class="btn btn-ghost" @click="cancel">Cancel</button>
        <button
          class="btn btn-primary"
          @click="saveNotes"
          :class="{ 'loading': isSaving }"
          :disabled="isSaving"
        >
          Save Notes
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMutation } from '@urql/vue';
import { getClient } from '../graphql/moneyPlans';

const props = defineProps<{
  planId: string;
  initialNotes: string;
}>();

const emit = defineEmits(['close', 'notesSaved']);

const noteText = ref(props.initialNotes || '');
const isSaving = ref(false);

const EDIT_PLAN_NOTES_MUTATION = `
  mutation editPlanNotes($input: EditPlanNotesInput!) {
    moneyPlan {
      editPlanNotes(input: $input) {
        success
        error {
          message
        }
        moneyPlan {
          id
          notes
        }
      }
    }
  }
`;

const { executeMutation } = useMutation(EDIT_PLAN_NOTES_MUTATION, {
  client: () => getClient()
});

function cancel() {
  emit('close');
}

async function saveNotes() {
  if (isSaving.value) return;
  
  isSaving.value = true;
  try {
    const result = await executeMutation({
      input: {
        planId: props.planId,
        notes: noteText.value
      }
    });
    
    if (result.error) {
      console.error('Error saving plan notes:', result.error);
      return;
    }
    
    if (result.data?.moneyPlan?.editPlanNotes?.success) {
      emit('notesSaved', result.data.moneyPlan.editPlanNotes.moneyPlan);
    } else {
      console.error('Failed to save plan notes:', 
        result.data?.moneyPlan?.editPlanNotes?.error?.message);
    }
  } catch (e) {
    console.error('Error saving plan notes:', e);
  } finally {
    isSaving.value = false;
    emit('close');
  }
}
</script>