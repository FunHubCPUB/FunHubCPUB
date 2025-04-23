document.getElementById('connectWallet').addEventListener('click', async () => {
    if (window.ethereum) {
        try {
            const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
            const walletAddress = accounts[0];

            const response = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ wallet_address: walletAddress })
            });

            const result = await response.json();
            if (result.status === 'success') {
                document.getElementById('status').innerText = "Wallet connected and verified!";
                window.location.href = "/editor";
            } else {
                document.getElementById('status').innerText = result.message;
            }
        } catch (error) {
            console.error(error);
            document.getElementById('status').innerText = "Failed to connect wallet!";
        }
    } else {
        document.getElementById('status').innerText = "MetaMask is not installed!";
    }
});

document.getElementById('switchNetwork').addEventListener('click', async () => {
    if (window.ethereum) {
        try {
            // Request account access
            await ethereum.request({ method: 'eth_requestAccounts' });

            const celoNetwork = {
                chainId: '0xa4ec', // Celo Mainnet Chain ID in hexadecimal
                chainName: 'Celo Mainnet',
                nativeCurrency: {
                    name: 'Celo',
                    symbol: 'CELO',
                    decimals: 18
                },
                rpcUrls: ['https://forno.celo.org'],
                blockExplorerUrls: ['https://explorer.celo.org']
            };

            try {
                // Attempt to switch to the Celo network
                await ethereum.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: celoNetwork.chainId }]
                });
                document.getElementById('status').innerText = "Switched to Celo network!";
            } catch (switchError) {
                // If the network is not added, add it
                if (switchError.code === 4902) {
                    try {
                        await ethereum.request({
                            method: 'wallet_addEthereumChain',
                            params: [celoNetwork]
                        });
                        document.getElementById('status').innerText = "Celo network added and switched!";
                    } catch (addError) {
                        console.error(addError);
                        document.getElementById('status').innerText = "Failed to add Celo network!";
                    }
                } else {
                    console.error(switchError);
                    document.getElementById('status').innerText = "Failed to switch to Celo network!";
                }
            }
        } catch (authError) {
            console.error(authError);
            document.getElementById('status').innerText = "Authorization required. Please connect your wallet.";
        }
    } else {
        document.getElementById('status').innerText = "MetaMask is not installed!";
    }
});