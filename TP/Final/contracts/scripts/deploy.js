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
    const hardhatSecondDerivationPath = "m/44'/60'/0'/0/1";
    const fundingWallet = ethers.HDNodeWallet.fromPhrase(
        HARDHAT_FUNDING_MNEMONIC, 
        null, 
        hardhatSecondDerivationPath
    ).connect(provider);

    // 1. Generar la billetera raíz para la suite de TEST (Python)
    const testMasterNode = ethers.HDNodeWallet.createRandom();
    const testMnemonicPhrase = testMasterNode.mnemonic.phrase;

    // Derivar las 3 cuentas requeridas por la suite de pruebas de Python
    const ownerWallet = ethers.HDNodeWallet.fromPhrase(testMnemonicPhrase, null, "m/44'/60'/0'/0/0").connect(provider);
    const funderWallet = ethers.HDNodeWallet.fromPhrase(testMnemonicPhrase, null, "m/44'/60'/0'/0/1").connect(provider);
    const adminWalletTest = ethers.HDNodeWallet.fromPhrase(testMnemonicPhrase, null, "m/44'/60'/0'/0/2").connect(provider);

    // 2. Generar un mnemónico NUEVO y separado para METAMASK
    const metamaskMasterNode = ethers.HDNodeWallet.createRandom();
    const metamaskMnemonicPhrase = metamaskMasterNode.mnemonic.phrase;
    
    // En MetaMask, el Admin será la primera dirección (index 0)
    const adminWalletMetaMask = ethers.HDNodeWallet.fromPhrase(metamaskMnemonicPhrase, null, "m/44'/60'/0'/0/0").connect(provider);

    // Obtención del nonce inicial
    let currentNonce = await provider.getTransactionCount(fundingWallet.address);

    console.log("Financiando cuentas del ecosistema...");

    // Fondear Owner (Test Index 0)
    const tx0 = await fundingWallet.sendTransaction({
        to: ownerWallet.address,
        value: ethers.parseEther("1000.0"),
        nonce: currentNonce++
    });
    await tx0.wait();

    // Fondear Funder (Test Index 1)
    const tx1 = await fundingWallet.sendTransaction({
        to: funderWallet.address,
        value: ethers.parseEther("1000.0"),
        nonce: currentNonce++
    });
    await tx1.wait();

    // Fondear Admin de Tests (Test Index 2)
    const tx2 = await fundingWallet.sendTransaction({
        to: adminWalletTest.address,
        value: ethers.parseEther("1000.0"),
        nonce: currentNonce++
    });
    await tx2.wait();

    // Lectura del artefacto e instalación del contrato usando el Owner
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

    // ================= CONFIGURACIÓN ENTORNO =================
    console.log("\n================ INFORMACIÓN GENERAL ================");
    console.log(`CFP_FACTORY_ADDRESS=${contractAddress}`);
    console.log(`CFP_MNEMONIC="${testMnemonicPhrase}"`);
    console.log("=======================================================\n");

    console.log("================ CONFIGURACIÓN DE TESTS (API) ================");
    console.log("Si se desea correr los test de la api, utilizar estas variables de entorno:");
    console.log(`CFP_ADMIN_ADDRESS=${adminWalletTest.address}`);
    //console.log(`CFP_ADMIN_PRIVATE_KEY=${adminWalletTest.privateKey}`);
    console.log("==============================================================\n");

    console.log("================ CONFIGURACIÓN METAMASK ================");
    console.log("Si se desea usar MetaMask, se puede usar este mnemónico:");
    console.log(`Mnemónico: "${metamaskMnemonicPhrase}"`);
    console.log(`La address del ADMIN es la primera dirección derivable (Index 0): ${adminWalletMetaMask.address}`);
    console.log(`NOTA: Las cuentas pertenecientes a este nmonico deben ser fondeadas por el script fund_acounts.js`)
    console.log("========================================================\n");
}

main().catch((error) => {
    console.error("Error en el proceso de despliegue:", error);
    process.exit(1);
});