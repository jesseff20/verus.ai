(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var providerField = document.getElementById('id_provider');
        var modelField = document.getElementById('id_model');

        if (!providerField || !modelField) return;

        var modelsCache = null;
        var currentModelValue = modelField.value;

        function fetchModels(callback) {
            if (modelsCache) { callback(modelsCache); return; }
            var xhr = new XMLHttpRequest();
            xhr.open('GET', './llm-models-json/');
            xhr.onload = function() {
                if (xhr.status === 200) {
                    modelsCache = JSON.parse(xhr.responseText);
                    callback(modelsCache);
                }
            };
            xhr.send();
        }

        function filterModels() {
            var selectedProvider = providerField.value;
            if (!selectedProvider) return;

            fetchModels(function(data) {
                var allowedModels = data[selectedProvider] || [];
                var allowedIds = allowedModels.map(function(m) { return m.id; });

                modelField.innerHTML = '';

                var emptyOpt = document.createElement('option');
                emptyOpt.value = '';
                emptyOpt.textContent = '--- Selecione o modelo ---';
                modelField.appendChild(emptyOpt);

                allowedModels.forEach(function(m) {
                    var opt = document.createElement('option');
                    opt.value = m.id;
                    opt.textContent = m.name;
                    if (m.id === currentModelValue) { opt.selected = true; }
                    modelField.appendChild(opt);
                });

                // Manter modelo salvo mesmo se não pertence ao provider (legado)
                if (currentModelValue && allowedIds.indexOf(currentModelValue) === -1) {
                    var legadoOpt = document.createElement('option');
                    legadoOpt.value = currentModelValue;
                    legadoOpt.textContent = currentModelValue + ' (legado)';
                    legadoOpt.selected = true;
                    modelField.appendChild(legadoOpt);
                }
            });
        }

        providerField.addEventListener('change', function() {
            currentModelValue = '';
            filterModels();
        });

        filterModels();
    });
})();
