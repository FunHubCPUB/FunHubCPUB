require('dotenv').config();
const HDWalletProvider = require('@truffle/hdwallet-provider');

module.exports = {
  networks: {
    celo: {
      provider: () => new HDWalletProvider(
        process.env.PRIVATE_KEY,
        'https://forno.celo.org' // Celo mainnet RPC
      ),
      network_id: 42220, // Celo mainnet network ID
      confirmations: 2,
      timeoutBlocks: 200,
      skipDryRun: true,
      from: process.env.WALLET_ADDRESS // Optional
    }
  },
  compilers: {
    solc: {
      version: '0.8.21', // Adjust to your contract requirements
    }
  }
};