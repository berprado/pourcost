const { ref, computed, onMounted } = Vue;

window.CocktailList = {
  emits: ["select"],
  setup(_, { emit }) {
    const cocktails = ref([]);
    const categories = ref([]);
    const search = ref("");
    const filterCat = ref("");
    const loading = ref(true);
    const error = ref("");

    onMounted(async () => {
      try {
        [cocktails.value, categories.value] = await Promise.all([
          window.api("/cocktails"),
          window.api("/cocktails/categories"),
        ]);
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    });

    const filtered = computed(() => {
      let list = cocktails.value;
      if (filterCat.value) list = list.filter(c => c.nombre_categoria_combo === filterCat.value);
      if (search.value) {
        const q = search.value.toLowerCase();
        list = list.filter(c => c.nombre_combo.toLowerCase().includes(q) || c.codigo_combo.includes(q));
      }
      return list;
    });

    function pourCostColor(precio) {
      if (!precio) return "";
      return "";
    }

    return { cocktails, categories, search, filterCat, loading, error, filtered };
  },
  template: `
    <div>
      <div class="flex items-center justify-between mb-3">
        <h2 style="font-size:1.15rem;font-weight:600">Menú de cócteles</h2>
        <span class="text-muted">{{ filtered.length }} ítems</span>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <div class="flex gap-2 mb-3">
        <input v-model="search" placeholder="Buscar por nombre o código..." style="max-width:320px" />
        <select v-model="filterCat" style="max-width:220px">
          <option value="">Todas las categorías</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div v-if="loading" class="text-muted">Cargando...</div>
      <div v-else class="card" style="padding:0;overflow:hidden">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Categoría</th>
              <th class="text-right">Precio</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in filtered"
              :key="c.id_combo_coctel"
              class="clickable"
              @click="$emit('select', c.id_combo_coctel)"
            >
              <td class="text-muted">{{ c.codigo_combo }}</td>
              <td>{{ c.nombre_combo }}</td>
              <td><span class="badge badge-ok">{{ c.nombre_categoria_combo }}</span></td>
              <td class="text-right text-gold">{{ c.precio_venta ? c.precio_venta.toFixed(2) + ' Bs' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
