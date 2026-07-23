import { expect } from "chai";
import hre from "hardhat";

describe("BENCOIN Contract", function () {
  let ethers;
  let bencoin;
  let owner, user1, user2;
  const RATE = 1000n;

  beforeEach(async function () {
    // Se inicializa el entorno y se obtienen las cuentas de prueba.
    ({ ethers } = await hre.network.getOrCreate());
    [owner, user1, user2] = await ethers.getSigners();

    // Se despliega el contrato estableciendo la tasa de cambio inicial.
    const BencoinFactory = await ethers.getContractFactory("BENCOIN");
    bencoin = await BencoinFactory.deploy(RATE);
  });

  describe("Despliegue e Inicialización", function () {
    it("debe asignar correctamente el nombre y el símbolo del token", async () => {
      // Se verifica que el contrato inicialice con los valores "BENCOIN" y "BEN".
      expect(await bencoin.name()).to.equal("BENCOIN");
      expect(await bencoin.symbol()).to.equal("BEN");
    });

    it("debe establecer la tasa de cambio correcta", async () => {
      // Se constata que la variable pública 'rate' coincida con el valor enviado en el constructor.
      expect(await bencoin.rate()).to.equal(RATE);
    });

    it("el suministro inicial debe ser cero", async () => {
      // Al heredar de ERC20 y no minar tokens en el constructor, el suministro total inicial debe ser 0.
      expect(await bencoin.totalSupply()).to.equal(0n);
    });
  });

  describe("Compra de tokens (buy)", function () {
    it("debe fallar si no se envía ETH en la transacción", async () => {
      // Se evalúa que la función exija un msg.value mayor a 0.
      await expect(
        bencoin.connect(user1).buy({ value: 0n })
      ).to.be.revertedWith("Debes enviar ETH");
    });

    it("debe minar la cantidad correcta de tokens y asignarlos al comprador", async () => {
      const ethAmount = ethers.parseEther("1"); // 1 ETH
      const expectedTokens = ethAmount * RATE; // Cálculo de la proporción (ETH * tasa).

      // Se ejecuta la compra.
      await bencoin.connect(user1).buy({ value: ethAmount });

      // Se verifica el saldo del usuario y el suministro total.
      const balance = await bencoin.balanceOf(user1.address);
      expect(balance).to.equal(expectedTokens);
      expect(await bencoin.totalSupply()).to.equal(expectedTokens);
    });

    it("debe aumentar el saldo de ETH del contrato inteligente", async () => {
      const ethAmount = ethers.parseEther("2");
      const contractAddress = await bencoin.getAddress();

      // Guardar el saldo de ETH del contrato ANTES de la compra
      const initialBalance = await ethers.provider.getBalance(contractAddress);

      // Ejecutar la compra
      await bencoin.connect(user1).buy({ value: ethAmount });

      // Guardar el saldo DESPUÉS de la compra
      const finalBalance = await ethers.provider.getBalance(contractAddress);

      // Verificar que el saldo del contrato haya aumentado exactamente en ethAmount
      expect(finalBalance - initialBalance).to.equal(ethAmount);
    });


  });

  describe("Venta de tokens (sell)", function () {
    beforeEach(async function () {
      // Se fondea a user1 con tokens antes de las pruebas de venta.
      await bencoin.connect(user1).buy({ value: ethers.parseEther("2") }); // user1 recibe 2000 BEN.
    });

    it("debe fallar si se intenta vender 0 tokens", async () => {
      // Se constata que la función bloquee la venta de 0 unidades.
      await expect(
        bencoin.connect(user1).sell(0n)
      ).to.be.revertedWith("Debes vender al menos 1 token");
    });

    it("debe fallar si el usuario no tiene saldo suficiente de tokens", async () => {
      const tooManyTokens = ethers.parseEther("3") * RATE; // 3000 BEN
      
      // Se verifica que no se puedan vender más tokens de los que posee el remitente.
      await expect(
        bencoin.connect(user1).sell(tooManyTokens)
      ).to.be.revertedWith("No tienes suficientes tokens");
    });

    it("debe quemar los tokens vendidos y devolver el ETH correspondiente", async () => {
      const tokensToSell = ethers.parseEther("1") * RATE; // 1000 BEN
      const expectedEthReturn = tokensToSell / RATE; // 1 ETH
      const contractAddress = await bencoin.getAddress();

      // Guardar los saldos de ETH del contrato ANTES de la venta
      const initialContractBalance = await ethers.provider.getBalance(contractAddress);

      // Ejecutar la venta
      await bencoin.connect(user1).sell(tokensToSell);

      // Guardar los saldos DESPUÉS
      const finalContractBalance = await ethers.provider.getBalance(contractAddress);

      // Verificar que los tokens del usuario hayan sido quemados
      const newBalance = await bencoin.balanceOf(user1.address);
      expect(newBalance).to.equal(ethers.parseEther("1") * RATE);

      // 2. Verificamos que el contrato haya entregado exactamente el ETH correspondiente
      expect(initialContractBalance - finalContractBalance).to.equal(expectedEthReturn);
    });
  });
});