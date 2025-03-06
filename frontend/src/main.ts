import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import urql, { cacheExchange, fetchExchange } from '@urql/vue';
import { createRouter, createWebHistory } from 'vue-router';
import IndexPage from './pages/index.vue';

const app = createApp(App);

app.use(urql, {
  url: 'http://localhost:8001/graphql/',
  exchanges: [cacheExchange, fetchExchange]
});

const routes = [
  { path: '/', component: IndexPage }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

app.use(router);
app.mount('#app');
