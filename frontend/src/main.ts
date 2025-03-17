import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import urql, { createClient, cacheExchange, fetchExchange } from '@urql/vue'
import App from './App.vue'
import './style.css'

// Import pages
import IndexPage from './pages/index.vue'
import PlansPage from './pages/plans.vue'

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: IndexPage },
    { path: '/plans', component: PlansPage },
  ],
})

// Create urql client
const client = createClient({
  url: 'http://localhost:8001/graphql/',
  exchanges: [cacheExchange, fetchExchange],
})

const app = createApp(App)
app.use(router)
app.use(urql, client) // Use the proper URQL Vue plugin setup
app.mount('#app')
