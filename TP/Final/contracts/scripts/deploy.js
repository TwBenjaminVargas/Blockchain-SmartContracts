import { ethers } from "ethers";
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RPC_URL = process.argv[2] ?? "http://127.0.0.1:8545";

// Mnemónico por defecto de la red local para proveer fondos iniciales
const HARDHAT_FUNDING_MNEMONIC = "test test test test test test test test test test test junk";

// Helper para leer artefactos de Hardhat de forma dinámica
function getArtifact(contractName) {
    const path = join(__dirname, `../artifacts/contracts/${contractName}.sol/${contractName}.json`);
    try {
        return JSON.parse(readFileSync(path, "utf8"));
    } catch (e) {
        throw new Error(`No se pudo leer el artefacto en la ruta: ${path}. Asegúrate de ejecutar 'npx hardhat compile' antes.`);
    }
}

// Función helper para calcular Namehash estándar de ENS en JS
function getNamehash(domain) {
    if (!domain) return ethers.ZeroHash;
    const parts = domain.split(".");
    let node = ethers.ZeroHash;
    for (let i = parts.length - 1; i >= 0; i--) {
        const labelHash = ethers.keccak256(ethers.toUtf8Bytes(parts[i]));
        node = ethers.solidityPackedKeccak256(["bytes32", "bytes32"], [node, labelHash]);
    }
    return node;
}

async function main() {
    const provider = new ethers.JsonRpcProvider(RPC_URL);

    // ================= 1. INICIALIZACIÓN DE CUENTAS DE ORIGEN (HARDHAT) =================
    // Cuenta para desplegar la infraestructura ENS (Index 0)
    const deployer = ethers.HDNodeWallet.fromPhrase(
        HARDHAT_FUNDING_MNEMONIC, 
        null, 
        "m/44'/60'/0'/0/0"
    ).connect(provider);

    // Cuenta pre-financiada para dar fondos iniciales a la suite de tests (Index 1)
    const fundingWallet = ethers.HDNodeWallet.fromPhrase(
        HARDHAT_FUNDING_MNEMONIC, 
        null, 
        "m/44'/60'/0'/0/1"
    ).connect(provider);

    console.log(`Desplegando ENS con la cuenta: ${deployer.address}`);
    console.log(`Fondeando ecosistema con la cuenta: ${fundingWallet.address}\n`);

    // ================= 2. GENERACIÓN Y FONDEO DE CUENTAS DEL ECOSISTEMA =================
    // Generar la billetera raíz para la suite de TEST (Python)
    const testMasterNode = ethers.HDNodeWallet.createRandom();
    const testMnemonicPhrase = testMasterNode.mnemonic.phrase;

    // Derivar las 3 cuentas requeridas por la suite de pruebas de Python
    const ownerWallet = ethers.HDNodeWallet.fromPhrase(testMnemonicPhrase, null, "m/44'/60'/0'/0/0").connect(provider);
    const funderWallet = ethers.HDNodeWallet.fromPhrase(testMnemonicPhrase, null, "m/44'/60'/0'/0/1").connect(provider);
    const adminWalletTest = ethers.HDNodeWallet.fromPhrase(testMnemonicPhrase, null, "m/44'/60'/0'/0/2").connect(provider);

    // Generar un mnemónico NUEVO y separado para METAMASK
    const metamaskMasterNode = ethers.HDNodeWallet.createRandom();
    const metamaskMnemonicPhrase = metamaskMasterNode.mnemonic.phrase;
    
    // En MetaMask, el Admin será la primera dirección (index 0)
    const adminWalletMetaMask = ethers.HDNodeWallet.fromPhrase(metamaskMnemonicPhrase, null, "m/44'/60'/0'/0/0").connect(provider);

    // Obtención del nonce inicial para fondear
    let fundingNonce = await provider.getTransactionCount(fundingWallet.address);

    console.log("Financiando cuentas de la suite de pruebas...");

    // Fondear Owner (Test Index 0)
    const tx0 = await fundingWallet.sendTransaction({
        to: ownerWallet.address,
        value: ethers.parseEther("1000.0"),
        nonce: fundingNonce++
    });
    await tx0.wait();

    // Fondear Funder (Test Index 1)
    const tx1 = await fundingWallet.sendTransaction({
        to: funderWallet.address,
        value: ethers.parseEther("1000.0"),
        nonce: fundingNonce++
    });
    await tx1.wait();

    // Fondear Admin de Tests (Test Index 2)
    const tx2 = await fundingWallet.sendTransaction({
        to: adminWalletTest.address,
        value: ethers.parseEther("1000.0"),
        nonce: fundingNonce++
    });
    await tx2.wait();
    console.log("-> Cuentas del ecosistema financiadas con éxito.\n");


    // ================= 3. DESPLIEGUE DE LA INFRAESTRUCTURA ENS (.cfp) =================
    let deployerNonce = await provider.getTransactionCount(deployer.address);

    // Desplegar Registry
    console.log("Desplegando contrato Registry...");
    const registryArtifact = getArtifact("Registry");
    const registryFactory = new ethers.ContractFactory(registryArtifact.abi, registryArtifact.bytecode, deployer);
    const registryContract = await registryFactory.deploy(deployer.address, { nonce: deployerNonce++ });
    await registryContract.waitForDeployment();
    const registryAddress = await registryContract.getAddress();
    console.log(`-> Registry desplegado en: ${registryAddress}\n`);

    // Desplegar Resolver Global
    console.log("Desplegando Public Resolver...");
    const resolverArtifact = getArtifact("Resolver");
    const resolverFactory = new ethers.ContractFactory(resolverArtifact.abi, resolverArtifact.bytecode, deployer);
    const resolverContract = await resolverFactory.deploy(registryAddress, { nonce: deployerNonce++ });
    await resolverContract.waitForDeployment();
    const resolverAddress = await resolverContract.getAddress();
    console.log(`-> Resolver desplegado en: ${resolverAddress}\n`);

    // Crear Dominio de Primer Nivel ".cfp"
    const cfpLabel = ethers.keccak256(ethers.toUtf8Bytes("cfp"));
    const cfpNode = getNamehash("cfp");

    console.log("Configurando Dominio Raíz '.cfp'...");
    const txCfp = await registryContract.setSubnodeOwner(ethers.ZeroHash, cfpLabel, deployer.address, { nonce: deployerNonce++ });
    await txCfp.wait();
    
    const txCfpResolver = await registryContract.setResolver(cfpNode, resolverAddress, { nonce: deployerNonce++ });
    await txCfpResolver.wait();
    console.log("-> '.cfp' configurado y asignado al Resolver.\n");

    // Crear Subdominio y FIFS Registrar para "usuarios.cfp"
    const usuariosLabel = ethers.keccak256(ethers.toUtf8Bytes("usuarios"));
    const usuariosNode = getNamehash("usuarios.cfp");

    console.log("Configurando subdominio 'usuarios.cfp'...");
    const txUsuarios = await registryContract.setSubnodeOwner(cfpNode, usuariosLabel, deployer.address, { nonce: deployerNonce++ });
    await txUsuarios.wait();

    const txUsuariosResolver = await registryContract.setResolver(usuariosNode, resolverAddress, { nonce: deployerNonce++ });
    await txUsuariosResolver.wait();

    console.log("Desplegando FIFSRegistrar para usuarios.cfp...");
    const usuariosRegistrarArtifact = getArtifact("Registrar");
    const usuariosRegistrarFactory = new ethers.ContractFactory(usuariosRegistrarArtifact.abi, usuariosRegistrarArtifact.bytecode, deployer);
    const usuariosRegistrarContract = await usuariosRegistrarFactory.deploy(registryAddress, usuariosNode, { nonce: deployerNonce++ });
    await usuariosRegistrarContract.waitForDeployment();
    const usuariosRegistrarAddress = await usuariosRegistrarContract.getAddress();

    const txTransferUsuarios = await registryContract.setOwner(usuariosNode, usuariosRegistrarAddress, { nonce: deployerNonce++ });
    await txTransferUsuarios.wait();
    console.log("-> Propiedad de 'usuarios.cfp' delegada al FIFSRegistrar de usuarios con éxito.\n");

    // Crear Subdominio "llamados.cfp"
    const llamadosLabel = ethers.keccak256(ethers.toUtf8Bytes("llamados"));
    const llamadosNode = getNamehash("llamados.cfp");

    console.log("Configurando subdominio 'llamados.cfp'...");
    const txLlamados = await registryContract.setSubnodeOwner(cfpNode, llamadosLabel, deployer.address, { nonce: deployerNonce++ });
    await txLlamados.wait();

    const txLlamadosResolver = await registryContract.setResolver(llamadosNode, resolverAddress, { nonce: deployerNonce++ });
    await txLlamadosResolver.wait();

    console.log("Desplegando FIFSRegistrar para llamados.cfp...");
    const llamadosRegistrarArtifact = getArtifact("Registrar");
    const llamadosRegistrarFactory = new ethers.ContractFactory(llamadosRegistrarArtifact.abi, llamadosRegistrarArtifact.bytecode, deployer);
    const llamadosRegistrarContract = await llamadosRegistrarFactory.deploy(registryAddress, llamadosNode, { nonce: deployerNonce++ });
    await llamadosRegistrarContract.waitForDeployment();
    const llamadosRegistrarAddress = await llamadosRegistrarContract.getAddress();

    const txTransferLlamados = await registryContract.setOwner(llamadosNode, llamadosRegistrarAddress, { nonce: deployerNonce++ });
    await txTransferLlamados.wait();
    console.log("-> Propiedad de 'llamados.cfp' delegada al FIFSRegistrar de llamados con éxito.\n");

    // Configurar Resolución Reversa (addr.reverse)
    console.log("Configurando Infraestructura de Resolución Reversa (EIP-181)...");
    const reverseLabel = ethers.keccak256(ethers.toUtf8Bytes("reverse"));
    const reverseNode = getNamehash("reverse");
    const addrLabel = ethers.keccak256(ethers.toUtf8Bytes("addr"));
    const addrReverseNode = getNamehash("addr.reverse");

    const txReverse = await registryContract.setSubnodeOwner(ethers.ZeroHash, reverseLabel, deployer.address, { nonce: deployerNonce++ });
    await txReverse.wait();

    const txAddrReverse = await registryContract.setSubnodeOwner(reverseNode, addrLabel, deployer.address, { nonce: deployerNonce++ });
    await txAddrReverse.wait();

    console.log("Desplegando ReverseRegistrar...");
    const reverseRegistrarArtifact = getArtifact("ReverseRegistrar");
    const reverseRegistrarFactory = new ethers.ContractFactory(reverseRegistrarArtifact.abi, reverseRegistrarArtifact.bytecode, deployer);
    const reverseRegistrarContract = await reverseRegistrarFactory.deploy(registryAddress, resolverAddress, { nonce: deployerNonce++ });
    await reverseRegistrarContract.waitForDeployment();
    const reverseRegistrarAddress = await reverseRegistrarContract.getAddress();

    const txTransferReverse = await registryContract.setOwner(addrReverseNode, reverseRegistrarAddress, { nonce: deployerNonce++ });
    await txTransferReverse.wait();
    console.log("-> Control de 'addr.reverse' transferido al ReverseRegistrar.\n");


    // ================= 4. DESPLIEGUE DE CFP_FACTORY =================
    console.log("Desplegando CFPFactory usando la cuenta Owner de pruebas...");
    const factoryArtifact = getArtifact("CFPFactory");
    const factory = new ethers.ContractFactory(factoryArtifact.abi, factoryArtifact.bytecode, ownerWallet);
    const contract = await factory.deploy();
    await contract.waitForDeployment();
    const contractAddress = await contract.getAddress();
    console.log(`-> CFPFactory desplegado en: ${contractAddress}\n`);


    // ================= 5. CONFIGURACIÓN FINAL / CONSOLA =================
    console.log("\n================= DESPLIEGUE FINALIZADO CON ÉXITO =================");
    console.log(`CFP_FACTORY_ADDRESS="${contractAddress}"`);
    console.log(`REGISTRY_ADDRESS="${registryAddress}"`);
    console.log(`RESOLVER_ADDRESS="${resolverAddress}"`);
    console.log(`REGISTRAR_USUARIOS_ADDRESS="${usuariosRegistrarAddress}"`);
    console.log(`REVERSE_REGISTRAR_ADDRESS="${reverseRegistrarAddress}"`);
    console.log(`LLAMADOS_REGISTRAR_ADDRESS="${llamadosRegistrarAddress}"`);
    console.log(`CFP_MNEMONIC="${testMnemonicPhrase}"`);
    console.log("====================================================================\n");

    console.log("================ CONFIGURACIÓN DE TESTS (API) ================");
    console.log("Si se desea correr los test de la api, utilizar estas variables de entorno:");
    console.log(`CFP_ADMIN_ADDRESS=${adminWalletTest.address}`);
    console.log("==============================================================\n");

    console.log("================ CONFIGURACIÓN METAMASK ================");
    console.log("Si se desea usar MetaMask, se puede usar este mnemónico:");
    console.log(`Mnemónico: "${metamaskMnemonicPhrase}"`);
    console.log(`La address del ADMIN es la primera dirección derivable (Index 0): ${adminWalletMetaMask.address}`);
    console.log(`NOTA: Las cuentas pertenecientes a este mnemónico deben ser fondeadas por el script fund_acounts.js`);
    console.log("========================================================\n");
}

main().catch((error) => {
    console.error("Error en el proceso de despliegue:", error);
    process.exit(1);
});