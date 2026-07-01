import { ethers } from "ethers";

const RPC_URL = "http://127.0.0.1:8545";
const HARDHAT_FUNDING_MNEMONIC = "test test test test test test test test test test test junk";

async function main() {
    // Capturar el mnemónico pasado por argumento
    const targetMnemonic = process.argv[2];

    if (!targetMnemonic) {
        console.error("❌ Error: Debes pasar el mnemónico objetivo como argumento entre comillas.");
        console.error('Ejemplo: node fund_accounts.js "bacon bacon bacon..."');
        process.exit(1);
    }

    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const fundingWallet = ethers.HDNodeWallet.fromPhrase(HARDHAT_FUNDING_MNEMONIC).connect(provider);

    let currentNonce = await provider.getTransactionCount(fundingWallet.address);
    const amountToFund = ethers.parseEther("1000.0");

    console.log(`\n================ FONDEANDO 10 CUENTAS ================`);
    console.log(`Fondeando desde: ${fundingWallet.address}`);
    console.log(`Monto por cuenta: 1000 ETH\n`);

    // Derivar y fondear las primeras 10 cuentas (indices del 0 al 9)
    for (let i = 0; i < 9; i++) {
        const path = `m/44'/60'/0'/0/${i}`;
        const targetWallet = ethers.HDNodeWallet.fromPhrase(targetMnemonic, null, path);
        
        console.log(`[${i}] Enviando a: ${targetWallet.address} (Path: ${path})...`);

        const tx = await fundingWallet.sendTransaction({
            to: targetWallet.address,
            value: amountToFund,
            nonce: currentNonce++
        });

        // Esperamos a que la transacción se confirme antes de avanzar para no romper el nonce en automining rígido
        await tx.wait(); 
    }

    console.log(`\n✅ ¡Proceso completado con éxito! 10 cuentas fondeadas.`);
    console.log(`======================================================\n`);
}

main().catch((error) => {
    console.error("Error ejecutando el fondeo:", error);
    process.exit(1);
});