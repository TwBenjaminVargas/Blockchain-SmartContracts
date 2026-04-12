// URL de API
const API_URL = 'http://127.0.0.1:5000';

// Elementos del DOM
const fileInput = document.getElementById('fileInput');
const fileButton = document.getElementById('fileButton');
const fileNameDisplay = document.getElementById('fileName');
const hashPreview = document.getElementById('hashPreview');
const signCheckbox = document.getElementById('signCheckbox');
const privateKeyInput = document.getElementById('privateKey');
const stampButton = document.getElementById('stampButton');
const resultBox = document.getElementById('resultBox');
const resultMessage = document.getElementById('resultMessage');

let currentHash = null;

// Disparar input de archivo
fileButton.addEventListener('click', () => {
    fileInput.click();
});

// Manejo del archivo seleccionado y cálculo de SHA-256
fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    fileNameDisplay.textContent = file.name;
    stampButton.disabled = true;
    hashPreview.classList.add('hidden');
    
    try {
        currentHash = await calculateSHA256(file);
        hashPreview.textContent = `Hash: ${currentHash}`;
        hashPreview.classList.remove('hidden');
        stampButton.disabled = false;
    } catch (error) {
        showResult(false, "Error calculando el hash del archivo.");
        console.error(error);
    }
});

// Habilitar/Deshabilitar input de clave privada
signCheckbox.addEventListener('change', (e) => {
    privateKeyInput.disabled = !e.target.checked;
    if (!e.target.checked) {
        privateKeyInput.value = '';
    }
});

// Stamping del archivo
stampButton.addEventListener('click', async () => {
    if (!currentHash) return;

    const usePrivateKey = signCheckbox.checked;
    const privateKey = privateKeyInput.value.trim();

    if (usePrivateKey && !privateKey) {
        showResult(false, "Debe ingresar una clave privada si marcó la opción.");
        return;
    }


    const payload = {
        hash: currentHash
    };

    try {
        stampButton.disabled = true;
        stampButton.textContent = "Procesando...";
        hideResult();

        // generacion de firma usando ethers.js
        if (usePrivateKey) {
            const formattedKey = privateKey.startsWith('0x') ? privateKey : `0x${privateKey}`;
            
            try {
                const wallet = new ethers.Wallet(formattedKey);
                const messageBytes = ethers.getBytes(currentHash);
                const signature = await wallet.signMessage(messageBytes);
                payload.signature = signature;
            } catch (err) {
                throw new Error("Clave privada inválida. Verifica el formato.");
            }
        }

        const response = await fetch(`${API_URL}/stamp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            const msg = `¡El archivo se registró con éxito!\nBlock Nro: ${data.blockNumber}\nTransacción: ${data.transaction}`;
            showResult(true, msg);
        } else {

            let errorMsg = `Error: ${data.message}`;
            if (data.blockNumber) {
                errorMsg += `\nRegistrado en bloque: ${data.blockNumber}\nFirmante: ${data.signer}`;
            }
            showResult(false, errorMsg);
        }

    } catch (error) {
        showResult(false, `Error de conexión o validación: ${error.message}`);
    } finally {
        stampButton.disabled = false;
        stampButton.textContent = "Stamp!";
    }
});

async function calculateSHA256(file) {
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return '0x' + hashHex;
}

function showResult(isSuccess, text) {
    resultBox.classList.remove('hidden', 'result-success', 'result-error');
    
    if (isSuccess) {
        resultBox.classList.add('result-success');
    } else {
        resultBox.classList.add('result-error');
    }
    
    resultMessage.innerHTML = text.replace(/\n/g, '<br>');
}

function hideResult() {
    resultBox.classList.add('hidden');
    resultMessage.innerHTML = '';
}