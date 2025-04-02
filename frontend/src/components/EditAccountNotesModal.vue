<template>
  <div class="modal modal-open">
    <div class="modal-box">
      <h3 class="font-bold text-lg">Edit Account Notes</h3>
      <p class="text-sm text-base-content/70 mt-1">{{ accountName }}</p>
      <div class="form-control w-full mt-4">
        <textarea
          class="textarea textarea-bordered h-32"
          placeholder="Enter your notes for this account"
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
  accountId: string;
  accountName: string;
  initialNotes: string;
}>();

const emit = defineEmits(['close', 'notesSaved']);

const noteText = ref(props.initialNotes || '');
const isSaving = ref(false);

const EDIT_ACCOUNT_NOTES_MUTATION = `
  mutation editAccountNotes($input: EditAccountNotesInput!) {
    moneyPlan {
      editAccountNotes(input: $input) {
        success
        error {
          message
        }
        moneyPlan {
          id
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
          initialBalance
          remainingBalance
          timestamp
          isCommitted
          isArchived
        }
      }
    }
  }
`;

const { executeMutation } = useMutation(EDIT_ACCOUNT_NOTES_MUTATION, {
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
        accountId: props.accountId,
        notes: noteText.value
      }
    });
    
    if (result.error) {
      console.error('Error saving account notes:', result.error);
      return;
    }
    
    if (result.data?.moneyPlan?.editAccountNotes?.success) {
      emit('notesSaved', result.data.moneyPlan.editAccountNotes.moneyPlan);
    } else {
      console.error('Failed to save account notes:', 
        result.data?.moneyPlan?.editAccountNotes?.error?.message);
    }
  } catch (e) {
    console.error('Error saving account notes:', e);
  } finally {
    isSaving.value = false;
    emit('close');
  }
}
</script>