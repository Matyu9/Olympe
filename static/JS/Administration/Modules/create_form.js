let config;

function create_form() {
    let files = document.getElementById('file-input').files;
    let modules_name = document.getElementById('modules-name');

    if (files.length !== 0 && modules_name.value === "autre") {
        let fr = new FileReader();

        fr.onload = async function(e) {
            console.log(e);
            let result = JSON.parse(e.target.result);
            config = JSON.stringify(result, null, 2);
            // console.log(config)
        }
        fr.readAsText(files.item(0));
        console.log(config)
    } else if (files.length === 0 && modules_name.value === "Autre") {
        alert('Veuillez sélectionner un fichier.')
    } else if (modules_name.value !== "autre") {
        fetch(`https://matyu.fr/cantina/Olympe/${modules_name.value.toLowerCase()}-install-file.json`, {
            method: 'GET',
            mode: "cors",
            headers: {
                'Accept': 'application/json',
            }
        })
            .then(response => response.json())
            .then(response => console.log(JSON.stringify(response)))
    }
}