<template>
  <button
    class="google-auth-btn"
    @click="handleGoogleLogin"
    :disabled="loading"
  >
    <img 
      src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg"
      alt="Google logo"
      class="google-icon"
    />
    {{ loading ? 'Loading...' : 'Continue with Google' }}
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMutation } from '@urql/vue';
import { GOOGLE_AUTH_URL } from '../graphql/auth';

const emit = defineEmits(['auth-success']);
const loading = ref(false);
const { executeMutation: getGoogleAuthUrl } = useMutation(GOOGLE_AUTH_URL);

async function handleGoogleLogin() {
  loading.value = true;
  try {
    const result = await getGoogleAuthUrl();
    if (result.data?.auth?.googleAuthUrl?.authUrl) {
      // Store the current page URL so we can return after authentication
      localStorage.setItem('googleAuthRedirect', window.location.href);
      window.location.href = result.data.auth.googleAuthUrl.authUrl;
    }
  } catch (error) {
    console.error('Error getting Google auth URL:', error);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.google-auth-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem;
  background-color: white;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.google-auth-btn:hover {
  background-color: #f8f8f8;
}

.google-auth-btn:disabled {
  background-color: #eee;
  cursor: not-allowed;
}

.google-icon {
  width: 18px;
  height: 18px;
}
</style>