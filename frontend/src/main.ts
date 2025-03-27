import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { urql } from '@urql/vue';
import App from './App.vue';
import router from './router';
import { client } from './graphql/client';
import './style.css';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(urql, client);

app.mount('#app');
