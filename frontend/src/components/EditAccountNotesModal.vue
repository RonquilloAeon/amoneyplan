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
        ... on Success {
          message
          data
        }
        ... on ApplicationError {
          message
        }
        ... on UnexpectedError {
          message
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
    
    const response = result.data.moneyPlan.editAccountNotes;
    
    // Check if we got an error response
    if (response.__typename === 'ApplicationError' || response.__typename === 'UnexpectedError') {
      console.error('Failed to save account notes:', response.message);
      return;
    }
    
    // Transform the data to match the frontend's expected structure
    const transformedData = {
      ...response.data,
      planDate: response.data.plan_date,
      isCommitted: response.data.is_committed,
      isArchived: response.data.is_archived,
      initialBalance: response.data.initial_balance,
      remainingBalance: response.data.remaining_balance,
      accounts: response.data.accounts.map(account => ({
        ...account,
        isChecked: account.is_checked,
        buckets: account.buckets.map(bucket => ({
          ...bucket,
          bucketName: bucket.bucket_name,
          allocatedAmount: bucket.allocated_amount
        }))
      }))
    };
    
    // Success! Emit the transformed plan
    emit('notesSaved', transformedData);
    emit('close');
  } catch (e) {
    console.error('Error saving account notes:', e);
  } finally {
    isSaving.value = false;
  }
}
</script>