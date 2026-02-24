const { ref, onMounted, watch } = Vue;

window.CocktailDetail = {
  props: ["cocktailId"],
  emits: ["back", "show-pourcost"],
  setup(props, { emit }) {
    const cocktail = ref(null);
    const selectedOptional = ref(null);
    const loading = ref(true);
    const error = ref("");

    async function load() {
      loading.value = true;
      error.value = "";
      cocktail.value = null;
      selectedOptional.value = null;
      try {
        cocktail.value = await window.api(`/cocktails/${props.cocktailId}`);
        if (cocktail.value.opcionales.length === 1) {
          selectedOptional.value = cocktail.value.opcionales[0].id_producto;
        }
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    onMounted(load);
    watch(() => props.cocktailId, load);

    function verPourCost() {
      emit("show-pourcost", {
        cocktailId: props.cocktailId,
        optionalId: selectedOptional.value,
      });
    }

    function fmtCantidad(ing) {
      return `${ing.cantidad_receta} ${ing.unidad_detalle}`;
    }

    return { cocktail, selectedOptional, loading, error, verPourCost, fmtCantidad };
  },
  template: `
    <div>
      <button class="btn btn-secondary btn-sm mb-3" @click="$emit('back')">← Volver</button>

      <div v-if="loading" class="text-muted">Cargando...</div>
      <div v-else-if="error" class="alert alert-error">{{ error }}</div>
      <div v-else-if="cocktail">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h2 style="font-size:1.2rem;font-weight:600">{{ cocktail.nombre_combo }}</h2>
            <span class="text-muted">{{ cocktail.nombre_categoria_combo }} · Precio: <span class="text-gold">{{ cocktail.precio_venta ? cocktail.precio_venta.toFixed(2) + ' Bs' : '—' }}</span></span>
          </div>
        </div>

        <!-- Ingredientes principales -->
        <div class="card mb-2">
          <h3 style="font-size:.9rem;font-weight:600;margin-bottom:.75rem;color:#888;text-transform:uppercase;letter-spacing:.06em">Ingredientes principales</h3>
          <table>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>Unidad base</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ing in cocktail.principales" :key="ing.id_producto">
                <td>{{ ing.nombre_producto }}</td>
                <td>{{ fmtCantidad(ing) }}</td>
                <td class="text-muted">{{ ing.unidad_base }}</td>
                <td>
                  <span v-if="ing.sin_wac" class="badge badge-warn" title="Sin WAC registrado">⚠ Sin costo</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Ingredientes opcionales -->
        <div v-if="cocktail.opcionales.length > 0" class="card mb-3">
          <h3 style="font-size:.9rem;font-weight:600;margin-bottom:.75rem;color:#888;text-transform:uppercase;letter-spacing:.06em">
            Elige un acompañante opcional
          </h3>
          <div v-for="ing in cocktail.opcionales" :key="ing.id_producto"
            style="display:flex;align-items:center;gap:.75rem;padding:.5rem;border-radius:7px;cursor:pointer;margin-bottom:.25rem"
            :style="selectedOptional === ing.id_producto ? 'background:#1e2e1e;border:1px solid #4caf82' : 'border:1px solid #2a2a3a'"
            @click="selectedOptional = ing.id_producto"
          >
            <span style="font-size:1rem">{{ selectedOptional === ing.id_producto ? '🟢' : '⚪' }}</span>
            <span>{{ ing.nombre_producto }}</span>
            <span class="text-muted" style="margin-left:auto">{{ fmtCantidad(ing) }}</span>
            <span v-if="ing.sin_wac" class="badge badge-warn">⚠ Sin costo</span>
          </div>
        </div>

        <button
          class="btn btn-primary"
          :disabled="cocktail.opcionales.length > 0 && !selectedOptional"
          @click="verPourCost"
        >
          Ver Pour Cost →
        </button>
        <p v-if="cocktail.opcionales.length > 0 && !selectedOptional" class="text-muted mt-1" style="font-size:.8rem">
          Selecciona un acompañante opcional para continuar
        </p>
      </div>
    </div>
  `,
};
