const { ref, onMounted, watch, computed } = Vue;

window.PourCostPanel = {
  props: ["cocktailId", "optionalId"],
  emits: ["back"],
  setup(props) {
    const result = ref(null);
    const loading = ref(true);
    const error = ref("");

    async function load() {
      loading.value = true;
      error.value = "";
      result.value = null;
      try {
        const path = props.optionalId
          ? `/cocktails/${props.cocktailId}/pourcost/${props.optionalId}`
          : `/cocktails/${props.cocktailId}/pourcost`;
        result.value = await window.api(path);
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    onMounted(load);
    watch(() => [props.cocktailId, props.optionalId], load);

    const pourCostClass = computed(() => {
      const pc = result.value?.pour_cost;
      if (!pc) return "";
      if (pc < 0.28) return "badge-ok";
      if (pc < 0.38) return "badge-warn";
      return "badge-danger";
    });

    const bs = window.fmtBs;
    const pct = window.fmtPct;
    function frac(v) {
      if (v == null) return "—";
      return new Intl.NumberFormat('es-BO', { minimumFractionDigits: 4, maximumFractionDigits: 4 }).format(v);
    }

    return { result, loading, error, pourCostClass, pct, bs, frac };
  },
  template: `
    <div>
      <button class="btn btn-secondary btn-sm mb-3" @click="$emit('back')">← Volver a receta</button>

      <div v-if="loading" class="text-muted">Calculando...</div>
      <div v-else-if="error" class="alert alert-error">{{ error }}</div>
      <div v-else-if="result">
        <div class="flex items-center justify-between mb-3">
          <h2 style="font-size:1.2rem;font-weight:600">{{ result.nombre_combo }}</h2>
          <span class="text-muted">Precio venta: <span class="text-gold">{{ bs(result.precio_venta) }}</span></span>
        </div>

        <!-- Alerta incompleto -->
        <div v-if="result.incompleto" class="alert" style="background:#3a2a10;border:1px solid #5a4a20;color:#c9a84c;margin-bottom:1rem">
          ⚠ <strong>COGS Incompleto</strong> — Uno o más ingredientes no tienen WAC registrado. El total no puede calcularse.
        </div>

        <!-- Tabla de ingredientes -->
        <div class="card mb-3" style="padding:0;overflow:hidden">
          <table>
            <thead>
              <tr>
                <th>Ingrediente</th>
                <th class="text-right">Cantidad</th>
                <th class="text-right">WAC / u.base</th>
                <th class="text-right">Fracción</th>
                <th class="text-right">COGS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ing in result.ingredientes" :key="ing.id_producto">
                <td>
                  {{ ing.nombre_producto }}
                  <span v-if="ing.sin_wac" class="badge badge-warn" style="margin-left:.4rem">⚠ Sin WAC</span>
                </td>
                <td class="text-right text-muted">{{ ing.cantidad_receta }} {{ ing.unidad_detalle }}</td>
                <td class="text-right">{{ bs(ing.wac_actual) }}</td>
                <td class="text-right text-muted">{{ frac(ing.cantidad_unidad_base) }}</td>
                <td class="text-right text-gold">{{ ing.sin_wac ? '—' : bs(ing.cogs_ingrediente) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Resumen -->
        <div class="card">
          <div class="grid-2" style="gap:1.5rem">
            <div>
              <div class="text-muted mb-1" style="font-size:.8rem;text-transform:uppercase;letter-spacing:.06em">COGS Total</div>
              <div style="font-size:1.4rem;font-weight:700;color:#e8e8ee">
                {{ result.incompleto ? '—' : bs(result.cogs_total) }}
              </div>
            </div>
            <div>
              <div class="text-muted mb-1" style="font-size:.8rem;text-transform:uppercase;letter-spacing:.06em">Margen</div>
              <div style="font-size:1.4rem;font-weight:700;color:#4caf82">
                {{ result.incompleto ? '—' : bs(result.margen) }}
              </div>
            </div>
            <div>
              <div class="text-muted mb-1" style="font-size:.8rem;text-transform:uppercase;letter-spacing:.06em">Utilidad</div>
              <div style="font-size:1.4rem;font-weight:700;color:#e8e8ee">
                {{ result.incompleto ? '—' : pct(result.margen / result.precio_venta) }}
              </div>
            </div>
            <div>
              <div class="text-muted mb-1" style="font-size:.8rem;text-transform:uppercase;letter-spacing:.06em">Pour Cost</div>
              <div style="font-size:1.4rem;font-weight:700">
                <span v-if="result.incompleto" class="text-muted">Incompleto ⚠</span>
                <span v-else :class="['badge', pourCostClass]" style="font-size:1.2rem;padding:.3rem .7rem">
                  {{ pct(result.pour_cost) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
};
