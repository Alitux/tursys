/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Filtro instantáneo de pasajeros en el detalle de excursión del portal.
 *
 * Filtra las tarjetas (móvil) y las filas de la tabla (escritorio) a medida
 * que el guía escribe, buscando por nombre, apellido, DNI/VAT, teléfono o
 * email. No distingue mayúsculas ni acentos y no recarga la página.
 */
publicWidget.registry.TursysPassengerFilter = publicWidget.Widget.extend({
    selector: ".o_tursys_pax_search",
    events: {
        "input .o_tursys_pax_input": "_onSearch",
        "search .o_tursys_pax_input": "_onSearch",
    },

    start() {
        this._input = this.el.querySelector(".o_tursys_pax_input");
        this._items = Array.from(this.el.querySelectorAll(".o_tursys_pax_item"));
        this._counter = this.el.querySelector(".o_tursys_pax_counter");
        this._noResult = this.el.querySelector(".o_tursys_pax_no_result");
        this._total = this._items.length;
        return this._super(...arguments);
    },

    _normalize(value) {
        return (value || "")
            .toString()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();
    },

    _onSearch() {
        if (!this._input) {
            return;
        }
        const query = this._normalize(this._input.value);
        let visible = 0;
        for (const item of this._items) {
            const haystack = this._normalize(item.dataset.paxSearch);
            const match = !query || haystack.includes(query);
            item.classList.toggle("d-none", !match);
            if (match) {
                visible += 1;
            }
        }
        if (this._counter) {
            this._counter.textContent =
                query && visible !== this._total ? `${visible} / ${this._total}` : "";
        }
        if (this._noResult) {
            this._noResult.classList.toggle("d-none", visible !== 0);
        }
    },
});

export default publicWidget.registry.TursysPassengerFilter;
