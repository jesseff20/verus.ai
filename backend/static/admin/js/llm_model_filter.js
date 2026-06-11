(function() {
    'use strict';

    // Espera o DOM carregar
    document.addEventListener('DOMContentLoaded', function() {
        var providerField = document.getElementById('id_llm_provider');
        var modelField = document.getElementById('id_model_name');

        if (!providerField || !modelField) return;

        // Cache dos modelos carregados da API
        var modelsCache = null;

        // Salvar o valor atual para restaurar depois do filtro
        var currentModelValue = modelField.value;

        // Salvar todas as options originais (agrupadas por optgroup)
        var originalGroups = {};
        var optgroups = modelField.querySelectorAll('optgroup');
        optgroups.forEach(function(group) {
            var options = [];
            group.querySelectorAll('option').forEach(function(opt) {
                options.push({ value: opt.value, text: opt.textContent });
            });
            originalGroups[group.label] = options;
        });

        // Mapeamento provider_code -> provider_name (buscar da API)
        function fetchModels(callback) {
            if (modelsCache) {
                callback(modelsCache);
                return;
            }
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

                // Limpar o select
                modelField.innerHTML = '';

                // Adicionar opção vazia
                var emptyOpt = document.createElement('option');
                emptyOpt.value = '';
                emptyOpt.textContent = '--- Selecione o modelo ---';
                modelField.appendChild(emptyOpt);

                // Adicionar modelos do provider selecionado
                if (allowedModels.length > 0) {
                    allowedModels.forEach(function(m) {
                        var opt = document.createElement('option');
                        opt.value = m.id;
                        opt.textContent = m.name;
                        if (m.id === currentModelValue) {
                            opt.selected = true;
                        }
                        modelField.appendChild(opt);
                    });
                }

                // Se o valor atual não pertence ao provider, verificar se é legado
                if (currentModelValue && allowedIds.indexOf(currentModelValue) === -1) {
                    // Manter como opção legada para não perder o valor salvo
                    var legadoOpt = document.createElement('option');
                    legadoOpt.value = currentModelValue;
                    legadoOpt.textContent = currentModelValue + ' (legado)';
                    legadoOpt.selected = true;
                    modelField.appendChild(legadoOpt);
                }
            });
        }

        // Filtrar ao mudar provider
        providerField.addEventListener('change', function() {
            currentModelValue = ''; // Reset ao mudar provider
            filterModels();
        });

        // Filtrar na carga inicial
        filterModels();
    });
})();
