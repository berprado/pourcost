const { createApp, ref, reactive } = Vue;

const app = createApp({
  template: `
    <template v-if="!auth.token">
      <login-form @logged-in="onLogin"></login-form>
    </template>
    <template v-else>
      <header>
        <h1>🍹 PourCost — BackStage Bar</h1>
        <span class="user">{{ auth.user?.nombres }} {{ auth.user?.paterno }}</span>
        <button class="logout btn btn-sm" @click="logout">Salir</button>
      </header>
      <main>
        <cocktail-list
          v-if="view === 'list'"
          @select="openDetail"
        ></cocktail-list>
        <cocktail-detail
          v-else-if="view === 'detail'"
          :cocktail-id="selectedId"
          @back="view = 'list'"
          @show-pourcost="openPourCost"
        ></cocktail-detail>
        <pour-cost-panel
          v-else-if="view === 'pourcost'"
          :cocktail-id="selectedId"
          :optional-id="selectedOptionalId"
          @back="view = 'detail'"
        ></pour-cost-panel>
      </main>
    </template>
  `,
  setup() {
    const auth = reactive({ token: null, user: null });
    const view = ref("list");
    const selectedId = ref(null);
    const selectedOptionalId = ref(null);

    function onLogin({ token, user }) {
      auth.token = token;
      auth.user = user;
      window.setToken(token);
      view.value = "list";
    }

    function logout() {
      auth.token = null;
      auth.user = null;
      window.clearToken();
      view.value = "list";
    }

    function openDetail(id) {
      selectedId.value = id;
      view.value = "detail";
    }

    function openPourCost({ cocktailId, optionalId }) {
      selectedId.value = cocktailId;
      selectedOptionalId.value = optionalId;
      view.value = "pourcost";
    }

    return { auth, view, selectedId, selectedOptionalId, onLogin, logout, openDetail, openPourCost };
  },
});

app.component("login-form", window.LoginForm);
app.component("cocktail-list", window.CocktailList);
app.component("cocktail-detail", window.CocktailDetail);
app.component("pour-cost-panel", window.PourCostPanel);

app.mount("#app");
