<template>
  <div class="auth-callback">
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else>Completing login...</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useMutation } from '@urql/vue';
import { GOOGLE_AUTH_CALLBACK } from '../graphql/auth';

const router = useRouter();
const authStore = useAuthStore();
const error = ref('');
const { executeMutation: googleCallback } = useMutation(GOOGLE_AUTH_CALLBACK);

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  
  if (!code) {
    error.value = 'Authentication code missing';
    setTimeout(() => router.push('/'), 3000);
    return;
  }

  try {
    const result = await googleCallback({ code });
    
    if (result.data?.auth?.googleCallback?.success) {
      // Update the auth store with the user data
      await authStore.setUser(result.data.auth.googleCallback.user);
      
      // Get the stored redirect URL or default to homepage
      const redirectUrl = localStorage.getItem('googleAuthRedirect') || '/';
      localStorage.removeItem('googleAuthRedirect'); // Clear stored URL
      
      router.push(redirectUrl);
    } else {
      error.value = result.data?.auth?.googleCallback?.error?.message || 'Authentication failed';
      setTimeout(() => router.push('/'), 3000);
    }
  } catch (err) {
    console.error('Error during Google auth callback:', err);
    error.value = 'An error occurred during authentication';
    setTimeout(() => router.push('/'), 3000);
  }
});
</script>

<style scoped>
.auth-callback {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.error {
  color: red;
}
</style>