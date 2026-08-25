function delete_account(){
    if (confirm('Êtes-vous sûr de vouloir supprimer ce compte ?')) {
        let form = document.getElementById('delete_account');
        let input = document.createElement("input");
        input.type = "hidden";
        form.appendChild(input);
        form.submit();
    } else {
        console.log('Annulation de la requete.');
    }
}