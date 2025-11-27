<template>
  <div>
    <h2>Access</h2>
    <div class="mb-3">
      <label class="form-label">Username</label>
      <input v-model="username" class="form-control form-control-dark" placeholder="admin" />
    </div>
    <div class="mb-3">
      <label class="form-label">Password</label>
      <input type="password" v-model="password" class="form-control form-control-dark" placeholder="password" />
    </div>
    <div class="mb-3">
      <button class="btn btn-primary" @click="doLogin">Login</button>
    </div>
    <div v-if="error" class="text-danger">{{ error }}</div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
    data() {
    return { username: '', password: '', error: null }
  },
  methods: {
    async doLogin() {
      try {
        const payload = { username: this.username, password: this.password }
        const res = await axios.post('/api/login', payload)
        const t = res.data.access_token
        const isAdmin = res.data.is_admin === true
        const mustChange = res.data.must_change === true
        // store token and set default header
        localStorage.setItem('eface_token', t)
        // persist admin flag for banner logic
        localStorage.setItem('eface_is_admin', isAdmin ? '1' : '0')
        axios.defaults.headers.common['Authorization'] = `Bearer ${t}`
        // don't store admin raw password anymore; rely on JWT is_admin claim
        if (mustChange) {
          this.$emit('must_change', { token: t })
        } else {
          this.$emit('logged', t)
        }
      } catch (e) {
        this.error = 'Login failed'
      }
    }
  }
}
</script>
