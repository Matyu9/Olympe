const STATUS_LABELS = {
    pending: 'En attente',
    cloning: 'Clonage du dépôt',
    registering: 'Enregistrement du module',
    configuring: 'Configuration',
    installing: 'Installation',
    done: 'Terminée',
    failed: 'Échec',
};

function status_label(status) {
    return STATUS_LABELS[status] || status;
}

function add_log_line(text) {
    const log = document.getElementById('progress-log');
    const line = document.createElement('li');
    line.textContent = text;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
}

document.addEventListener('DOMContentLoaded', function () {
    const main = document.getElementById('install-progress-main');
    const installationId = main.dataset.installationId;

    add_log_line(`Statut initial : ${status_label(main.dataset.status)}`);

    const socket = io();

    socket.on('connect', function () {
        socket.emit('join_install_room', {installation_id: installationId});
    });

    socket.on('module_install_progress', function (data) {
        document.getElementById('status-badge').textContent = status_label(data.status);
        if (data.message) {
            add_log_line(data.message);
        } else {
            add_log_line(`Étape : ${status_label(data.status)}`);
        }
    });

    socket.on('module_install_done', function (data) {
        document.getElementById('status-badge').textContent = status_label('done');
        document.getElementById('done-client-id').textContent = data.module_token;
        document.getElementById('done-client-secret').textContent = data.plain_secret;
        document.getElementById('done-panel').classList.remove('hidden');
    });

    socket.on('module_install_error', function (data) {
        document.getElementById('status-badge').textContent = status_label('failed');
        document.getElementById('error-message').textContent = data.message;
        document.getElementById('error-panel').classList.remove('hidden');
    });
});
