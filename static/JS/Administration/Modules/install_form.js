let manifest = null;

function render_manifest_preview() {
    document.getElementById('manifest-preview').classList.remove('hidden');
    document.getElementById('manifest-name').textContent = manifest.name || '';
    document.getElementById('manifest-repo').textContent = manifest['url-repo'] || '';
    document.getElementById('manifest-guidelines').textContent = manifest.guidelines || '';
    document.getElementById('manifest-beta').textContent = manifest.beta ? 'Oui' : 'Non';
    document.getElementById('manifest-install-script').textContent = manifest.configuration && manifest.configuration['install-script'] || '';

    const container = document.getElementById('html-input-fields');
    container.innerHTML = '';
    const htmlInput = (manifest.configuration && manifest.configuration['html-input']) || {};

    for (const key in htmlInput) {
        const field = htmlInput[key];
        const wrapper = document.createElement('div');
        wrapper.className = 'bg-base-200 p-4 rounded-lg';

        const label = document.createElement('div');
        label.className = 'text-sm opacity-70 mb-1';
        label.textContent = key;
        wrapper.appendChild(label);

        let input;
        if (field.type === 'checkbox') {
            input = document.createElement('input');
            input.type = 'checkbox';
            input.className = 'toggle';
            input.checked = field['default-value'] === 'true' || field['default-value'] === true;
        } else {
            input = document.createElement('input');
            input.type = field.type || 'text';
            input.className = 'input w-full max-w-xs';
            input.value = field['default-value'] || '';
        }
        input.name = `html_input__${key}`;
        wrapper.appendChild(input);
        container.appendChild(wrapper);
    }
}

function on_manifest_file_change() {
    const files = document.getElementById('manifest-file').files;
    if (files.length === 0) {
        return;
    }

    const reader = new FileReader();
    reader.onload = function (event) {
        try {
            manifest = JSON.parse(event.target.result);
        } catch (e) {
            alert('Le fichier sélectionné n\'est pas un JSON valide.');
            return;
        }
        document.getElementById('manifest-json').value = event.target.result;
        render_manifest_preview();
    };
    reader.readAsText(files.item(0));
}

function on_install_target_change() {
    const isRemote = document.getElementById('target-remote').checked;
    document.getElementById('ssh-fields').classList.toggle('hidden', !isRemote);
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('manifest-file').addEventListener('change', on_manifest_file_change);
    document.getElementById('target-local').addEventListener('change', on_install_target_change);
    document.getElementById('target-remote').addEventListener('change', on_install_target_change);
});
