import hre from "hardhat";

async function main() {
  const mnemonic = process.env.CFP_MNEMONIC;
  if (!mnemonic) {
    console.error("ERROR: CFP_MNEMONIC no está definida en el entorno.");
    process.exit(1);
  }

  //Inicializamos el entorno de Hardhat 3 de forma asíncrona
  const { ethers } = await hre.network.getOrCreate();

  // Derivamos la cuenta exacta de la consigna usando el objeto ethers resuelto
  const derivationPath = "m/44'/60'/0'/0/0";
  const deployerWallet = ethers.Wallet.fromPhrase(mnemonic.trim(), derivationPath);
  
  //Conectamos la billetera al proveedor de la red actual
  const deployer = deployerWallet.connect(ethers.provider);

  console.log(`\nIniciando despliegue...`);
  console.log(`Billetera emisora requerida: ${deployer.address}`);

  // Le pasamos explícitamente el 'deployer' derivado a la fábrica
  const CFPFactory = await ethers.getContractFactory("CFPFactory", deployer);
  const cfpFactory = await CFPFactory.deploy();

  await cfpFactory.waitForDeployment();

  const deployedAddress = await cfpFactory.getAddress();

  console.log("====================================================================");
  console.log(`CFPFactory desplegado en: ${deployedAddress}`);
  console.log("====================================================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});