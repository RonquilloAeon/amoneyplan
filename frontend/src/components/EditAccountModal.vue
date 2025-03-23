<template>
  <dialog ref="dialogRef" id="edit-account-modal" class="modal" :class="{ 'modal-open': isOpen }">
    <div class="modal-box relative max-w-md w-11/12">
      <h3 class="font-bold text-lg mb-4">Edit Account: {{ accountName }}</h3>
      
      <div class="alert alert-info mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <div>
          <div class="font-semibold">Remaining Balance</div>
          <div class="text-lg">${{ remainingBalance.toFixed(2) }}</div>
        </div>
      </div>
      
      <form @submit.prevent="updateAccount">
        <div class="divider">Buckets</div>
        
        <div v-for="(bucket, index) in buckets" :key="index" class="bg-base-200 p-3 rounded-md mb-3">
          <div class="flex justify-between items-center mb-2">
            <h4 class="font-semibold">Bucket #{{ index + 1 }}</h4>
            <button 
              type="button" 
              @click="removeBucket(index)" 
              class="btn btn-sm btn-ghost btn-circle"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="w-5 h-5 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <div class="form-control w-full mb-2">
            <label class="label py-1">
              <span class="label-text">Bucket Name</span>
            </label>
            <input 
              v-model="bucket.bucketName" 
              type="text" 
              placeholder="e.g. Emergency Fund"
              class="input input-bordered input-sm w-full" 
              required 
            />
          </div>
          
          <div class="form-control w-full mb-2">
            <label class="label py-1">
              <span class="label-text">Category</span>
            </label>
            <select 
              v-model="bucket.category" 
              class="select select-bordered select-sm w-full"
              required
            >
                <option disabled value="">Select category</option>
                <option value="Allowance">Allowance</option>
                <option value="Beauty">Beauty</option>
                <option value="Bills">Bills</option>
                <option value="Cash">Cash</option>
                <option value="Checking">Checking</option>
                <option value="Childcare">Childcare</option>
                <option value="Clothing">Clothing</option>
                <option value="Credit Card">Credit Card</option>
                <option value="Dining">Dining</option>
                <option value="Donations">Donations</option>
                <option value="Dry Powder">Dry Powder</option>
                <option value="Education">Education</option>
                <option value="Emergency Fund">Emergency Fund</option>
                <option value="Entertainment">Entertainment</option>
                <option value="Family">Family</option>
                <option value="Fitness">Fitness</option>
                <option value="Fun">Fun</option>
                <option value="Gifts">Gifts</option>
                <option value="Groceries">Groceries</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Hobbies">Hobbies</option>
                <option value="Insurance">Insurance</option>
                <option value="Investing">Investing</option>
                <option value="Loan">Loan</option>
                <option value="Misc">Misc</option>
                <option value="Mortgage">Mortgage</option>
                <option value="Other">Other</option>
                <option value="Personal Care">Personal Care</option>
                <option value="Pets">Pets</option>
                <option value="Remittance">Remittance</option>
                <option value="Rent">Rent</option>
                <option value="Savings">Savings</option>
                <option value="Subscriptions">Subscriptions</option>
                <option value="Taxes">Travel</option>
                <option value="Transportation">Transportation</option>
                <option value="Travel">Travel</option>
                <option value="Unexpected">Unexpected</option>
                <option value="Utilities">Utilities</option>
            </select>
          </div>
          
          <div class="form-control w-full">
            <label class="label py-1">
              <span class="label-text">Allocated Amount</span>
            </label>
            <input 
              v-model="bucket.allocatedAmount" 
              type="number" 
              step="0.01"
              class="input input-bordered input-sm w-full" 
              required 
              @input="validateTotalAmount"
            />
          </div>
        </div>
        
        <div class="flex justify-center my-3">
          <button 
            type="button" 
            @click="addBucket" 
            class="btn btn-outline btn-sm"
          >
            Add Bucket
          </button>
        </div>
        
        <div v-if="errorMessage" class="alert alert-error mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span>{{ errorMessage }}</span>
        </div>
        
        <div class="modal-action">
          <button type="button" @click="$emit('close')" class="btn btn-ghost">Cancel</button>
          <button 
            type="submit" 
            class="btn btn-primary"
            :disabled="!isValid || isSaving"
          >
            <span v-if="isSaving" class="loading loading-spinner loading-xs mr-1"></span>
            Save Changes
          </button>
        </div>
      </form>
      
      <form method="dialog">
        <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2" @click="$emit('close')">✕</button>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop" @submit="$emit('close')">
      <button>close</button>
    </form>
  </dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useMutation } from '@urql/vue';
import gql from 'graphql-tag';

const dialogRef = ref<HTMLDialogElement | null>(null);
const emit = defineEmits(['close', 'accountUpdated']);

interface Bucket {
  bucketName: string;
  category: string;
  allocatedAmount: number;
}

const props = defineProps<{
  planId: string;
  accountId: string;
  accountName: string;
  originalBuckets: Bucket[];
  currentAccountTotal: number;
  currentRemainingBalance: number;
  isChecked: boolean;
  isOpen: boolean;
}>();

// Watch for isOpen changes to show/close the dialog
watch(() => props.isOpen, (newValue) => {
  if (!dialogRef.value) return;
  
  if (newValue) {
    dialogRef.value.showModal();
    resetForm(); // Reset form when opening
  } else {
    dialogRef.value.close();
  }
});

// Close dialog when clicking outside or pressing escape
onMounted(() => {
  if (!dialogRef.value) return;
  
  dialogRef.value.addEventListener('close', () => {
    emit('close');
  });
});

// Form state
const errorMessage = ref('');
const isSaving = ref(false);
const buckets = ref<Bucket[]>(props.originalBuckets.map(b => ({...b})));

// Computed remaining balance 
const totalBucketAmount = computed(() => {
  return buckets.value.reduce((sum, bucket) => {
    return sum + Number(bucket.allocatedAmount);
  }, 0);
});

const remainingBalance = computed(() => {
  // Add back the original account total to the current remaining balance
  const availableBalance = props.currentRemainingBalance + props.currentAccountTotal;
  return availableBalance - totalBucketAmount.value;
});

const isValid = computed(() => {
  return buckets.value.length > 0 && 
    buckets.value.every(b => b.bucketName.trim() !== '' && b.category && b.allocatedAmount > 0) &&
    remainingBalance.value >= 0;
});

// Watch for changes in bucket amounts
watch(buckets, validateTotalAmount, { deep: true });

// Add/remove bucket methods
function addBucket() {
  buckets.value.push({
    bucketName: '',
    category: '',
    allocatedAmount: 0
  });
}

function removeBucket(index: number) {
  if (buckets.value.length > 1) {
    buckets.value.splice(index, 1);
  }
}

function validateTotalAmount() {
  if (remainingBalance.value < 0) {
    errorMessage.value = `Total bucket amount exceeds available balance by $${Math.abs(remainingBalance.value).toFixed(2)}`;
  } else {
    errorMessage.value = '';
  }
}

// GraphQL mutation
const CHANGE_ACCOUNT_CONFIGURATION_MUTATION = gql`
  mutation changeAccountConfiguration($input: AccountConfigurationChangeInput!) {
    moneyPlan {
      changeAccountConfiguration(input: $input) {
        error {
          message
        }
        success
        moneyPlan {
          id
          accounts {
            id
            name
            buckets {
              bucketName
              allocatedAmount
              category
            }
          }
          initialBalance
          remainingBalance
          timestamp
        }
      }
    }
  }
`;

const { executeMutation } = useMutation(CHANGE_ACCOUNT_CONFIGURATION_MUTATION);

async function updateAccount() {
  isSaving.value = true;
  errorMessage.value = '';

  try {
    const variables = { 
      input: {
        planId: props.planId,
        accountId: props.accountId,
        newBucketConfig: buckets.value.map(b => ({
          bucketName: b.bucketName,
          allocatedAmount: Number(b.allocatedAmount),
          category: b.category
        }))
      }
    };
    
    const response = await executeMutation(variables);
    
    if (response.error) {
      errorMessage.value = response.error.message;
      return;
    }
    
    if (response.data.moneyPlan.changeAccountConfiguration.error) {
      errorMessage.value = response.data.moneyPlan.changeAccountConfiguration.error.message;
      return;
    }
    
    // Success! Emit update event first
    emit('accountUpdated', response.data.moneyPlan.changeAccountConfiguration.moneyPlan);
    // Then close the modal which will trigger the close event handler
    emit('close');
  } catch (error) {
    errorMessage.value = (error as Error).message;
  } finally {
    isSaving.value = false;
  }
}

// Toggle account check mutation
const SET_ACCOUNT_CHECKED_STATE_MUTATION = gql`
  mutation setAccountCheckedState($input: SetAccountCheckedStateInput!) {
    moneyPlan {
      setAccountCheckedState(input: $input) {
        success
        error {
          message
        }
        moneyPlan {
          id
          accounts {
            id
            name
            isChecked
            notes
            buckets {
              bucketName
              category
              allocatedAmount
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

const { executeMutation: executeSetCheckedState } = useMutation(SET_ACCOUNT_CHECKED_STATE_MUTATION);

async function toggleAccountCheck() {
  try {
    const response = await executeSetCheckedState({
      input: {
        planId: props.planId,
        accountId: props.accountId,
        isChecked: !props.isChecked
      }
    });

    if (response.error) {
      errorMessage.value = response.error.message;
      return;
    }

    if (response.data.moneyPlan.setAccountCheckedState.error) {
      errorMessage.value = response.data.moneyPlan.setAccountCheckedState.error.message;
      return;
    }

    // Success! Emit update event
    emit('accountUpdated', response.data.moneyPlan.setAccountCheckedState.moneyPlan);
    
    // Close the modal after successful toggle
    emit('close');
  } catch (error) {
    errorMessage.value = (error as Error).message;
  }
}

function resetForm() {
  buckets.value = props.originalBuckets.map(b => ({...b}));
  errorMessage.value = '';
}

// Reset form when modal closes
watch(() => props.isOpen, (newValue) => {
  if (!newValue) {
    resetForm();
  }
});
</script>