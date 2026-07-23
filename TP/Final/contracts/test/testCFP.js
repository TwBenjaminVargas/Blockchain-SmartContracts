import { expect } from "chai";
import hre from "hardhat";
import { HashGenerator, emptyAddress } from "./shared.js";

let ethers;
let networkHelpers;
let accounts;
let defaultToken;
let tokenAddress;

before(async function () {
  ({ ethers, networkHelpers } = await hre.network.getOrCreate());
  accounts = await ethers.getSigners();

  // Se inicializa el token de prueba empleado para simular cobros de garantía en el contrato CFP.
  const Token = await ethers.getContractFactory("BENCOIN");
  defaultToken = await Token.deploy(1000n);
  tokenAddress = await defaultToken.getAddress();
});

const gen = new HashGenerator();

describe("Call for Proposals", function () {
  describe("Inicialización del contrato", function () {
    let closingTime;
    let cfp;
    let callId;

    before(async function () {
      callId = gen.next();
      const latestBlock = await ethers.provider.getBlock("latest");
      closingTime = latestBlock.timestamp + 100;
      const CFP = await ethers.getContractFactory("CFP");

      // Se instancia el contrato enviando los nuevos argumentos estructurales: admin, garantía (0) y token.
      cfp = await CFP.deploy(
        callId,
        BigInt(closingTime),
        accounts[0].address,
        0n,
        tokenAddress
      );
    });

    it("no debe haber propuestas", async () => {
      expect(await cfp.proposalCount()).to.equal(0n);
    });

    it("tiene que tener el callId correcto", async () => {
      expect(await cfp.callId()).to.equal(callId);
    });

    it("tiene que tener el tiempo de cierre correcto", async () => {
      expect(await cfp.closingTime()).to.equal(BigInt(closingTime));
    });

    it("debe tener el creador correcto", async () => {
      expect(await cfp.creator()).to.equal(accounts[0].address);
    });
  });

  describe("Inicialización incorrecta del contrato", function () {
    it("debe rechazar tiempos de cierre que están en el pasado", async () => {
      const currentBlock = await ethers.provider.getBlock("latest");
      const CFP = await ethers.getContractFactory("CFP");
      await expect(
        CFP.deploy(
          gen.next(),
          BigInt(currentBlock.timestamp),
          accounts[0].address,
          0n,
          tokenAddress
        )
      ).to.be.revertedWith(
        "El cierre de la convocatoria no puede estar en el pasado"
      );
    });
  });

  describe("Registro de propuestas sin garantía", function () {
    let initialBlock;
    let lastBlock;
    let cfp;
    let proposalCount;
    let closingTime;
    const proposals = [];

    before(async function () {
      initialBlock = await ethers.provider.getBlock("latest");
      closingTime = initialBlock.timestamp + 100;
      const CFP = await ethers.getContractFactory("CFP");

      cfp = await CFP.deploy(
        gen.get(0),
        BigInt(closingTime),
        accounts[0].address,
        0n,
        tokenAddress
      );

      proposalCount = 5 + Math.trunc(Math.random() * 10);
      for (let i = 0; i < proposalCount; i++) {
        const proposal = gen.next();
        await cfp.registerProposal(proposal);
        proposals.push(proposal);
      }
      lastBlock = await ethers.provider.getBlock("latest");
    });

    it("debe devolver la cantidad correcta de propuestas", async () => {
      expect(await cfp.proposalCount()).to.equal(BigInt(proposalCount));
    });

    it("debe devolver todas las propuestas registradas", async () => {
      for (let i = 0; i < proposalCount; i++) {
        expect(await cfp.proposals(i)).to.equal(proposals[i]);
      }
    });

    it("no debe tener propuestas que no han sido registradas", async () => {
      await expect(cfp.proposals(proposalCount)).to.be.rejected;
    });

    it("debe devolver números de bloque plausibles", async () => {
      const initialBlockNumber = BigInt(initialBlock.number);
      const lastBlockNumber = BigInt(lastBlock.number);
      let prevBlockNumber = initialBlockNumber;
      for (let i = 0; i < proposalCount; i++) {
        const proposalData = await cfp.proposalData(proposals[i]);
        const pbn = proposalData.blockNumber;
        expect(pbn >= prevBlockNumber).to.be.true;
        expect(pbn <= lastBlockNumber).to.be.true;
        prevBlockNumber = pbn;
      }
    });

    it("debe devolver información de tiempo correcta", async () => {
      for (let i = 0; i < proposalCount; i++) {
        const proposalData = await cfp.proposalData(proposals[i]);
        const block = await ethers.provider.getBlock(
          Number(proposalData.blockNumber)
        );
        expect(proposalData.timestamp).to.equal(BigInt(block.timestamp));
        expect(await cfp.proposalTimestamp(proposals[i])).to.equal(
          BigInt(block.timestamp)
        );
      }
    });

    it("debe devolver el emisor correcto", async () => {
      for (let i = 0; i < proposalCount; i++) {
        const proposalData = await cfp.proposalData(proposals[i]);
        expect(proposalData.sender).to.equal(accounts[0].address);
      }
    });

    it("debe rechazar propuestas que ya han sido registradas con registerProposal", async () => {
      await expect(cfp.registerProposal(proposals[0])).to.be.revertedWith(
        "La propuesta ya ha sido registrada"
      );
    });

    it("debe permitir que el creador use registerProposalFor", async () => {
      const proposal = gen.next();
      await cfp.registerProposalFor(proposal, accounts[1].address);
      const proposalData = await cfp.proposalData(proposal);
      expect(proposalData.sender).to.equal(accounts[1].address);
    });

    it("no debe permitir que quien no es creador pueda usar registerProposalFor", async () => {
      await expect(
        cfp
          .connect(accounts[2])
          .registerProposalFor(gen.next(), accounts[3].address)
      ).to.be.revertedWith("Solo el creador puede hacer esta llamada");
    });

    it("debe permitir que quien no es creador pueda usar registerProposal", async () => {
      const proposal = gen.next();
      const sender = accounts[2];
      await cfp.connect(sender).registerProposal(proposal);
      const proposalData = await cfp.proposalData(proposal);
      expect(proposalData.sender).to.equal(sender.address);
    });

    it("debe rechazar propuestas que ya han sido registradas con registerProposalFor", async () => {
      await expect(
        cfp.registerProposalFor(proposals[1], accounts[1].address)
      ).to.be.revertedWith("La propuesta ya ha sido registrada");
    });

    it("debe emitir el evento ProposalRegistered al registrar con registerProposal", async () => {
      const proposal = gen.next();
      const tx = cfp.registerProposal(proposal);
      const receipt = await (await tx).wait();
      const blockNumber = BigInt(receipt.blockNumber);
      await expect(tx)
        .to.emit(cfp, "ProposalRegistered")
        .withArgs(proposal, accounts[0].address, blockNumber);
    });

    it("debe emitir el evento ProposalRegistered al registrar con registerProposalFor", async () => {
      const proposal = gen.next();
      const tx = cfp.registerProposalFor(proposal, accounts[1].address);
      const receipt = await (await tx).wait();
      const blockNumber = BigInt(receipt.blockNumber);
      await expect(tx)
        .to.emit(cfp, "ProposalRegistered")
        .withArgs(proposal, accounts[1].address, blockNumber);
    });

    it("debe devolver información correcta para una propuesta no registrada", async () => {
      const proposal = gen.next();
      const proposalData = await cfp.proposalData(proposal);
      expect(proposalData.blockNumber).to.equal(0n);
      expect(proposalData.timestamp).to.equal(0n);
      expect(proposalData.sender).to.equal(emptyAddress);
      expect(await cfp.proposalTimestamp(proposal)).to.equal(0n);
    });
  });

  describe("Registro de propuestas con cobro de Garantía (BENCOIN)", function () {
    let cfpGuaranteed;
    let guaranteeAmount;

    before(async function () {
      const latestBlock = await ethers.provider.getBlock("latest");
      const closingTime = latestBlock.timestamp + 1000;
      guaranteeAmount = ethers.parseEther("5"); // Se establece un requerimiento de 5 BENCOINS

      const CFP = await ethers.getContractFactory("CFP");

      // Se instancia el contrato definiendo un valor estricto de garantía superior a cero.
      cfpGuaranteed = await CFP.deploy(
        gen.next(),
        BigInt(closingTime),
        accounts[0].address,
        guaranteeAmount,
        tokenAddress
      );

      // Se simula la adquisición de tokens por parte del proponente (accounts[1])
      // Enviando 0.01 ETH, obtendrá 10 BENCOINs (debido al rate de 1000 asignado en la factoría del token)
      await defaultToken.connect(accounts[1]).buy({ value: ethers.parseEther("0.01") });
    });

    it("debe fallar si el proponente no ha aprobado la transferencia del token de garantía", async () => {
      const proposal = gen.next();

      // Se verifica que la transacción revierta debido a la falta de allowance o saldo en el token ERC20.
      await expect(
        cfpGuaranteed.connect(accounts[1]).registerProposal(proposal)
      ).to.be.revertedWith(/allowance|balance|transfer/i);
    });
    it("debe permitir el registro descontando la garantía si se aprueban los tokens correspondientes", async () => {
      const cfpAddress = await cfpGuaranteed.getAddress();
      const proposal = gen.next();

      // Se aprueba la provisión de fondos a favor del contrato CFP.
      await defaultToken.connect(accounts[1]).approve(cfpAddress, guaranteeAmount);

      // Se concreta el registro de la propuesta.
      await cfpGuaranteed.connect(accounts[1]).registerProposal(proposal);

      // Se valida que el saldo del contrato CFP refleje de manera estricta la recepción de los activos fungibles requeridos como garantía.
      const cfpBalance = await defaultToken.balanceOf(cfpAddress);
      expect(cfpBalance).to.equal(guaranteeAmount);

      const proposalData = await cfpGuaranteed.proposalData(proposal);
      expect(proposalData.sender).to.equal(accounts[1].address);
    });
  });

  describe("Cierre de convocatoria", function () {
    it("debe rechazar propuestas enviadas después del cierre", async () => {
      const latestBlock = await ethers.provider.getBlock("latest");
      const closingTime = latestBlock.timestamp + 10;
      const CFP = await ethers.getContractFactory("CFP");

      const cfp = await CFP.deploy(
        gen.next(),
        BigInt(closingTime),
        accounts[0].address,
        0n,
        tokenAddress
      );

      await networkHelpers.time.increaseTo(closingTime + 1);
      await expect(cfp.registerProposal(gen.next())).to.be.revertedWith(
        "Convocatoria cerrada"
      );
    });
  });
});