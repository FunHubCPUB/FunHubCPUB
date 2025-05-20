const FUNNFT = artifacts.require("FUNNFT");
const CPUBToken = artifacts.require("CPUBToken");
module.exports = async function (deployer, network, accounts) {
    // Deploy FUNNFT with baseURI and initialOwner
    const baseURI = "https://funhub.lol/metadata/";
    await deployer.deploy(FUNNFT, baseURI, accounts[0]);

    // Deploy CPUBToken with initialOwner
    await deployer.deploy(CPUBToken, accounts[0]);
};