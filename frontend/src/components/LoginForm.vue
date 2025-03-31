<!-- Login form component -->
<template>
  <div class="login-form">
    <h2>Login</h2>
    <GoogleAuthButton class="mb-4" @auth-success="handleGoogleSuccess" />
    <div class="divider">or</div>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="username">Username</label>
        <input
          type="text"
          id="username"
          v-model="username"
          required
          autocomplete="username"
        />
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input
          type="password"
          id="password"
          v-model="password"
          required
          autocomplete="current-password"
        />
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
    <p>
      Don't have an account?
      <a href="#" @click.prevent="$emit('switch-to-register')">Register</a>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMutation } from '@urql/vue';
import { LOGIN_MUTATION } from '../graphql/auth';
import GoogleAuthButton from './GoogleAuthButton.vue';

const emit = defineEmits(['auth-success', 'switch-to-register']);

const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);

const { executeMutation: login } = useMutation(LOGIN_MUTATION);

async function handleSubmit() {
  loading.value = true;
  error.value = '';
  
  try {
    const result = await login({
      username: username.value,
      password: password.value,
    });
    
    if (result.data?.auth?.login?.success) {
      emit('auth-success', result.data.auth.login.user);
    } else {
      error.value = result.data?.auth?.login?.error?.message || 'Login failed';
    }
  } catch (e) {
    error.value = 'An error occurred during login';
  } finally {
    loading.value = false;
  }
}

function handleGoogleSuccess(user) {
  emit('auth-success', user);
}
</script>

<style scoped>
.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.error {
  color: red;
  margin-bottom: 1rem;
}

button {
  width: 100%;
  padding: 0.75rem;
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 1rem 0;
  color: #6b7280;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #e5e7eb;
}

.divider:not(:empty)::before {
  margin-right: 1rem;
}

.divider:not(:empty)::after {
  margin-left: 1rem;
}

.mb-4 {
  margin-bottom: 1rem;
}
</style>