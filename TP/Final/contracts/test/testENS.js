import { expect } from "chai";
import hre from "hardhat";

describe("Sistema ENS Completo", function () {
  let ethers;
  let owner, user1, user2, targetAccount;
  let registry, resolver, reverseRegistrar, usuariosRegistrar, llamadosRegistrar;

  const ZERO_HASH = "0x0000000000000000000000000000000000000000000000000000000000000000";

  beforeEach(async function () {
    // Inicializar el entorno de ethers desde hre
    ({ ethers } = await hre.network.getOrCreate());

    // Obtener las cuentas de prueba
    [owner, user1, user2, targetAccount] = await ethers.getSigners();

    // Desplegar contrato Registry
    const Registry = await ethers.getContractFactory("Registry");
    registry = await Registry.deploy(owner.address);

    // Desplegar contrato Resolver
    const Resolver = await ethers.getContractFactory("Resolver");
    resolver = await Resolver.deploy(registry.target);

    // Desplegar contrato ReverseRegistrar
    const ReverseRegistrar = await ethers.getContractFactory("ReverseRegistrar");
    reverseRegistrar = await ReverseRegistrar.deploy(registry.target, resolver.target);

    // Configurar la jerarquía inversa (addr.reverse)
    await registry.setSubnodeOwner(ZERO_HASH, ethers.id("reverse"), owner.address);
    await registry.setSubnodeOwner(
      ethers.namehash("reverse"), 
      ethers.id("addr"), 
      reverseRegistrar.target
    );

    // Configurar la jerarquía directa (cfp -> usuarios.cfp / llamados.cfp)
    await registry.setSubnodeOwner(ZERO_HASH, ethers.id("cfp"), owner.address);
    await registry.setSubnodeOwner(ethers.namehash("cfp"), ethers.id("usuarios"), owner.address);
    await registry.setSubnodeOwner(ethers.namehash("cfp"), ethers.id("llamados"), owner.address);

    // Desplegar UsuariosRegistrar
    const UsuariosRegistrar = await ethers.getContractFactory("UsuariosRegistrar");
    usuariosRegistrar = await UsuariosRegistrar.deploy(
      registry.target,
      resolver.target,
      ethers.namehash("usuarios.cfp"),
      reverseRegistrar.target,
      "usuarios.cfp"
    );

    // Desplegar LlamadosRegistrar
    const LlamadosRegistrar = await ethers.getContractFactory("LlamadosRegistrar");
    llamadosRegistrar = await LlamadosRegistrar.deploy(
      registry.target,
      resolver.target,
      ethers.namehash("llamados.cfp"),
      reverseRegistrar.target,
      "llamados.cfp"
    );

    // Ceder la propiedad de los nodos a los contratos registradores correspondientes
    await registry.setOwner(ethers.namehash("usuarios.cfp"), usuariosRegistrar.target);
    await registry.setOwner(ethers.namehash("llamados.cfp"), llamadosRegistrar.target);
  });

  describe("Configuración Inicial", function () {
    it("Validar la asignación del nodo raíz al propietario", async function () {
      expect(await registry.owner(ZERO_HASH)).to.equal(owner.address);
    });

    it("Validar la asignación del nodo addr.reverse al contrato ReverseRegistrar", async function () {
      expect(await registry.owner(ethers.namehash("addr.reverse"))).to.equal(reverseRegistrar.target);
    });
  });

  describe("UsuariosRegistrar", function () {
    it("Registrar un subdominio y configurar resolución directa e inversa", async function () {
      const label = "alice";
      const expectedDomain = "alice.usuarios.cfp";
      const node = ethers.namehash(expectedDomain);

      // Ejecutar registro
      await usuariosRegistrar.connect(user1).register(label);

      // Verificar propiedad en Registry
      expect(await registry.owner(node)).to.equal(user1.address);

      // Verificar resolución directa en Resolver
      expect(await registry.resolver(node)).to.equal(resolver.target);
      expect(await resolver.addr(node)).to.equal(user1.address);

      // Verificar resolución inversa calculando el nodo inverso de la wallet
      const reverseNode = ethers.namehash(`${user1.address.toLowerCase().substring(2)}.addr.reverse`);
      expect(await resolver.name(reverseNode)).to.equal(expectedDomain);
    });

    it("Revertir al intentar registrar un subdominio previamente asignado", async function () {
      const label = "bob";
      await usuariosRegistrar.connect(user1).register(label);

      // Intentar registrar el mismo nombre de dominio con un usuario distinto
      await expect(
        usuariosRegistrar.connect(user2).register(label)
      ).to.be.revertedWith("Nombre ya registrado por otro usuario");
    });
  });

  describe("LlamadosRegistrar", function () {
    it("Registrar un subdominio sin configurar los registros automáticamente", async function () {
      const label = "proyecto";
      const node = ethers.namehash("proyecto.llamados.cfp");

      // Ejecutar registro inicial
      await llamadosRegistrar.connect(user2).register(label);

      // Verificar propiedad
      expect(await registry.owner(node)).to.equal(user2.address);

      // Verificar que no se haya asignado dirección de resolución aún
      expect(await resolver.addr(node)).to.equal(ethers.ZeroAddress);
    });

    it("Configurar los registros de un subdominio previamente registrado", async function () {
      const label = "api";
      const node = ethers.namehash("api.llamados.cfp");

      // Ejecutar registro inicial
      await llamadosRegistrar.connect(user1).register(label);

      // Ejecutar configuración de registros apuntando a una dirección objetivo
      await llamadosRegistrar.connect(user1).setupRecords(label, targetAccount.address);

      // Verificar resolución directa actualizada
      expect(await resolver.addr(node)).to.equal(targetAccount.address);
    });

    it("Revertir si un usuario no propietario intenta configurar los registros", async function () {
      const label = "privado";
      
      await llamadosRegistrar.connect(user1).register(label);

      // Intentar configurar el subdominio utilizando un usuario sin permisos
      await expect(
        llamadosRegistrar.connect(user2).setupRecords(label, targetAccount.address)
      ).to.be.revertedWith("No eres el dueno de este subdominio");
    });
  });
});