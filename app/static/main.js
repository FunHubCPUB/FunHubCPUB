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