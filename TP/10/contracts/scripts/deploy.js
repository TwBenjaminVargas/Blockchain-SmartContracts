import { ethers } from "ethers";
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RPC_URL = process.argv[2] ?? "http://127.0.0.1:8545";

// Mnemónico por defecto de la red local para proveer fondos iniciales
const HARDHAT_FUNDING_MNEMONIC = "test test test test test test test test test test test junk";

async function main() {
    const provider = new ethers.JsonRpcProvider(RPC_URL);

    // Cuenta pre-financiada de la red local
    const fundingWallet = ethers.HDNodeWallet.fromPhrase(HARDHAT_FUNDING_MNEMONIC).connect(provider);

    // 1. Generar la billetera raíz (Mnemónico aleatorio para la sesión de pruebas)
    const masterNode = ethers.HDNodeWallet.createRandom();
    const mnemonicPhrase = masterNode.mnemonic.phrase;

    // 2. Derivar las 3 cuentas requeridas por la suite de pruebas de Python
    const ownerWallet = ethers.HDNodeWallet.fromPhrase(mnemonicPhrase, null, "m/44'/60'/0'/0/0").connect(provider);
    const funderWallet = ethers.HDNodeWallet.fromPhrase(mnemonicPhrase, null, "m/44'/60'/0'/0/1").connect(provider);
    const adminWallet = ethers.HDNodeWallet.fromPhrase(mnemonicPhrase, null, "m/44'/60'/0'/0/2").connect(provider);

    // Obtención del nonce inicial para evitar colisiones con automining
    let currentNonce = await provider.getTransactionCount(fundingWallet.address);

    console.log("Financiando cuentas del ecosistema...");

    // Fondear Owner (Index 0)
    const tx0 = await fundingWallet.sendTransaction({
        to: ownerWallet.address,
        value: ethers.parseEther("10.0"),
        nonce: currentNonce++
    });
    await tx0.wait();

    // Fondear Funder (Index 1)
    const tx1 = await fundingWallet.sendTransaction({
        to: funderWallet.address,
        value: ethers.parseEther("10.0"),
        nonce: currentNonce++
    });
    await tx1.wait();

    // Fondear Admin (Index 2)
    const tx2 = await fundingWallet.sendTransaction({
        to: adminWallet.address,
        value: ethers.parseEther("10.0"),
        nonce: currentNonce++
    });
    await tx2.wait();

    // Lectura del artefacto e instalación del contrato usando el Owner (Index 0)
    const { abi, bytecode } = JSON.parse(
        readFileSync(
            join(__dirname, "../artifacts/contracts/CFPFactory.sol/CFPFactory.json"),
            "utf8"
        )
    );

    const factory = new ethers.ContractFactory(abi, bytecode, ownerWallet);
    const contract = await factory.deploy();
    await contract.waitForDeployment();

    const contractAddress = await contract.getAddress();

    // Impresión formateada de las variables de entorno requeridas
    console.log("\n================ CONFIGURACIÓN ENTORNO ================");
    console.log(`CFP_FACTORY_ADDRESS=${contractAddress}`);
    console.log(`CFP_MNEMONIC="${mnemonicPhrase}"`);
    console.log(`CFP_ADMIN_ADDRESS=${adminWallet.address}`);
    console.log("=======================================================\n");
}

main().catch((error) => {
    console.error("Error en el proceso de despliegue:", error);
    process.exit(1);
});