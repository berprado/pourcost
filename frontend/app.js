const { createApp, ref, reactive } = Vue;

const app = createApp({
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
