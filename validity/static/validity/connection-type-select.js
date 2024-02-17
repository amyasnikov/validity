function fillTextArea(public_creds, private_creds) {
    document.getElementById('id_public_credentials').value = JSON.stringify(public_creds, null, 2);
    document.getElementById('id_private_credentials').value = JSON.stringify(private_creds, null, 2);
}

function fillCredentials(connectionTypeInfo) {
    try {
        const connectionType = connectionTypeInfo.value;
        if (connectionType == "")
            return;
        const defaultCredentials = JSON.parse(document.getElementById('default_credentials').textContent)[connectionType];
        fillTextArea(defaultCredentials.public, defaultCredentials.private);
    } catch(e) {
        console.log(e.name, e.message)
    }

}

window.onload = () => {document.getElementById('connection_type_select').slim.onChange = fillCredentials}
