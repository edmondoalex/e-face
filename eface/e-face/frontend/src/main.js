import { createApp } from 'vue'
import App from './App.vue'
import './styles.css'
import axios from './api'

// load token from localStorage if present
const token = localStorage.getItem('eface_token')
if (token) axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

createApp(App).mount('#app')
