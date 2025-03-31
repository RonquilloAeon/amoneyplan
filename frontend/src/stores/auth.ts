import { ref } from 'vue';
import { defineStore } from 'pinia';
import { useMutation, useQuery } from '@urql/vue';
import { ME_QUERY, LOGOUT_MUTATION } from '../graphql/auth';

export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const loading = ref(true);

  const { executeQuery } = useQuery({ query: ME_QUERY });
  const { executeMutation: logout } = useMutation(LOGOUT_MUTATION);

  async function checkAuth() {
    loading.value = true;
    try {
      const result = await executeQuery();
      user.value = result.data?.me || null;
    } finally {
      loading.value = false;
    }
  }

  async function setUser(newUser: User) {
    user.value = newUser;
  }

  async function handleLogout() {
    await logout();
    user.value = null;
  }

  // Check auth status on store initialization
  checkAuth();

  return {
    user,
    loading,
    checkAuth,
    setUser,
    handleLogout,
  };
});