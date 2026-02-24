const { ref } = Vue;

window.LoginForm = {
  emits: ["logged-in"],
  setup(_, { emit }) {
    const usuario = ref("");
    const contrasena = ref("");
    const error = ref("");
    const loading = ref(false);

    async function login() {
      error.value = "";
      loading.value = true;
      try {
        const data = await window.api("/auth/login", {
          method: "POST",
          body: JSON.stringify({ usuario: usuario.value, contrasena: contrasena.value }),
        });
        const me = await (async () => {
          window.setToken(data.access_token);
          return window.api("/auth/me");
        })();
        emit("logged-in", { token: data.access_token, user: me });
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    return { usuario, contrasena, error, loading, login };
  },
  template: `
    <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0f0f14">
      <div class="card" style="width:340px">
        <h2 class="text-gold mb-3" style="font-size:1.3rem;text-align:center">🍹 PourCost</h2>
        <p class="text-muted mb-3" style="text-align:center">BackStage Bar</p>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div class="mb-2">
          <label>Usuario</label>
          <input v-model="usuario" @keyup.enter="login" placeholder="usuario" autocomplete="username" />
        </div>
        <div class="mb-3">
          <label>Contraseña</label>
          <input v-model="contrasena" @keyup.enter="login" type="password" placeholder="••••••••" autocomplete="current-password" />
        </div>
        <button class="btn btn-primary w-full" :disabled="loading" @click="login">
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>
      </div>
    </div>
  `,
};
