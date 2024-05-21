function fillTextArea(public_creds, private_creds) {
    document.getElementById('id_public_credentials').value = JSON.stringify(public_creds, null, 2);
    document.getElementById('id_private_credentials').value = JSON.stringify(private_creds, null, 2);
}

function fillCredentials(valueExtracter, connectionTypeInfo) {
    try {
        const connectionType = valueExtracter(connectionTypeInfo)
        if (connectionType == "")
            return;
        const defaultCredentials = JSON.parse(document.getElementById('default_credentials').textContent)[connectionType];
        fillTextArea(defaultCredentials.public, defaultCredentials.private);
    } catch(e) {
        console.log(e.name, e.message)
    }

}

window.onload = () => {
    const select = document.getElementById('connection_type_select');
    if ("tomselect" in select) // NetBox 4.x
        select.tomselect.on("change", fillCredentials.bind(undefined, (value) => value))
    else // NetBox 3.x
        select.slim.onChange = fillCredentials.bind(undefined, (value) => value.value)
}
