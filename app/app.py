import uuid
from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import subprocess
from web3 import Web3
import json
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import urllib.parse
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

wallet_address_env = os.getenv('WALLET_ADDRESS')
if not wallet_address_env:
    raise ValueError("WALLET_ADDRESS environment variable not set.")
OWNER_ADDRESS = Web3.to_checksum_address(wallet_address_env)

PRIVATE_KEY = os.getenv('PRIVATE_KEY')
FUNNFT_ADDRESS = os.getenv('FUNNFT_ADDRESS')
CELO_RPC = os.getenv("CELO_RPC")
app.secret_key = os.getenv("SECRET_KEY")
CPUB_ADDRESS = os.getenv('CPUB_ADDRESS')

w3 = Web3(Web3.HTTPProvider(CELO_RPC))

FUNNFT_ABI_PATH = os.path.join(os.path.dirname(__file__), 'funnft_abi.json')
with open(FUNNFT_ABI_PATH, 'r') as abi_file:
    funnft_abi = json.load(abi_file)
funnft_contract = w3.eth.contract(address=Web3.to_checksum_address(FUNNFT_ADDRESS), abi=funnft_abi)

CPUB_ABI_PATH = os.path.join(os.path.dirname(__file__), 'cpub_abi.json')
with open(CPUB_ABI_PATH, 'r') as abi_file:
    cpub_abi = json.load(abi_file)
cpub_contract = w3.eth.contract(address=Web3.to_checksum_address(CPUB_ADDRESS), abi=cpub_abi)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def mint_and_return_receipt(title, description, wallet_address, cpub_amount):
    try:
        if not wallet_address or not Web3.is_address(wallet_address):
            raise Exception("Invalid or missing wallet address.")

        wallet_address = Web3.to_checksum_address(wallet_address)  # Ensure checksum

        account = w3.eth.account.from_key(PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)

        txn = funnft_contract.functions.mint(
            wallet_address,
            title,
            description
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 800000,
            'gasPrice': w3.eth.gas_price
        })
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        tx_hash_hex = receipt.transactionHash.hex()
        gas_fee_eth = (receipt.gasUsed * w3.eth.gas_price) / 1e18

        token_id = None
        if receipt and receipt.logs:
            for log in receipt.logs:
                try:
                    event = funnft_contract.events.Minted().processLog(log)
                    token_id = event['args']['tokenId']
                    break
                except Exception:
                    continue
        if token_id is None:
            token_id = funnft_contract.functions.nextTokenId().call()

        cpub_txn = cpub_contract.functions.mintTo(wallet_address, cpub_amount).build_transaction({
            'from': account.address,
            'nonce': nonce + 1,
            'gas': 800000,
            'gasPrice': w3.eth.gas_price
        })
        signed_cpub_txn = w3.eth.account.sign_transaction(cpub_txn, private_key=PRIVATE_KEY)
        cpub_tx_hash = w3.eth.send_raw_transaction(signed_cpub_txn.raw_transaction)
        cpub_receipt = w3.eth.wait_for_transaction_receipt(cpub_tx_hash)
        cpub_tx_hash_hex = cpub_receipt.transactionHash.hex()

        return tx_hash_hex, gas_fee_eth, receipt, token_id, cpub_tx_hash_hex
    except Exception as e:
        import traceback
        print(f"Error minting NFT or CPUB token: {e}")
        traceback.print_exc()
        return None, None, None, None, None

@app.route('/')
def index():
    return render_template('app.html')

@app.route('/mint', methods=['GET', 'POST'])
def mint():
    if request.method == 'POST':
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        wallet_address = request.form.get('wallet_address', '').strip()
        cpub_amount = int(request.form.get('cpub_amount', 1))
        if cpub_amount not in [1, 10, 100]:
            flash("Invalid CPUB amount.")
            return redirect(url_for('mint'))

        tx_hash, gas_fee_eth, receipt, token_id, cpub_tx_hash = mint_and_return_receipt(
            title, description, wallet_address, cpub_amount
        )
        if not tx_hash:
            flash("Minting failed.")
            return redirect(url_for('mint'))

        # --- Begin file operations and git workflow ---
        current_dir = os.getcwd()
        OUTPUT_DIR = os.path.join(current_dir, 'html')
        JSON_DIR = os.path.join(current_dir, 'metadata')
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(JSON_DIR, exist_ok=True)

        image_url = "https://funhub.lol/app/images/default.jpg"  # Or get from form/upload if available
        username = request.form.get('username', 'anonymous')

        # Generate EVM address for metadata
        evm_address = generate_evm_address()

        # Write JSON metadata with description as the link to the token's HTML page
        json_content = {
            "id": token_id,
            "name": title,
            "description": f"https://funhub.lol/app/html/{token_id}.html",
            "image": image_url,
            "external_url": f"https://funhub.lol/app/html/{token_id}.html",
            "attributes": [
                {"trait_type": "Creator", "value": username},
                {"trait_type": "Wallet", "value": wallet_address},
                {"trait_type": "Token ID", "value": evm_address},
                {"trait_type": "celo", "value": cpub_amount}
            ],
            "cpub_score": cpub_amount
        }
        with open(os.path.join(JSON_DIR, f"{token_id}.json"), "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)

        # Write HTML page for the NFT
        with open(os.path.join(OUTPUT_DIR, f"{token_id}.html"), "w", encoding="utf-8") as f:
            f.write(render_template('nft.html', image=image_url,
                                    title=title,
                                    body=image_url + "\n\n" + description,
                                    username=username,
                                    wallet_address=wallet_address,
                                    token_id=token_id,
                                    cpub_score=cpub_amount))

        # Update NFT index page (nfts.html) with all NFTs
        nft_entries = []
        for entry in get_json_file_names(JSON_DIR):
            try:
                with open(os.path.join(JSON_DIR, entry), "r", encoding="utf-8") as f:
                    nft_entries.append(json.load(f))
            except Exception as e:
                print(f"Error loading {entry}: {e}")
        nft_entries_sorted = sorted(nft_entries, key=get_token_id, reverse=True)
        # Write the nfts.html file to the OUTPUT_DIR so it is always updated
        with open(os.path.join(OUTPUT_DIR, 'nfts.html'), "w", encoding="utf-8") as f:
            f.write(render_template('nfts.html', entries=nft_entries_sorted))
        # Optionally, also write to current_dir for legacy support
        with open(os.path.join(current_dir, 'nfts.html'), "w", encoding="utf-8") as f:
            f.write(render_template('nfts.html', entries=nft_entries_sorted))

        subprocess.run(["/bin/bash", "github_workflow.sh"], check=True)
        # --- End file operations and git workflow ---

        return render_template(
            'success.html',
            tx_hash=tx_hash,
            gas_fee_eth=gas_fee_eth,
            receipt=receipt,
            token_id=token_id,
            cpub_tx_hash=cpub_tx_hash
        )

    return render_template('mint.html')

def git_push_with_ssh(commit_message="Auto commit"):
    # Start SSH agent and add key
    result = subprocess.run(["ssh-agent", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    for line in output.splitlines():
        if "SSH_AUTH_SOCK" in line or "SSH_AGENT_PID" in line:
            key, value = line.split(";", 1)[0].split("=", 1)
            os.environ[key] = value
    ssh_key_path = os.path.expanduser("~/id_rsa.pub")  # This should be id_rsa, not id_rsa.pub
    subprocess.run(["ssh-add", ssh_key_path], check=True)

    # Git add, commit, push
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=False)
    subprocess.run(["git", "push"], check=True)


@app.route('/policy')
def policy():
    return render_template('policy.html')






import os
import subprocess

def get_json_file_names(directory):
    if not os.path.exists(directory):
        return []
    return [file for file in os.listdir(directory) if file.endswith('.json')]

def get_token_id(entry):
    try:
        for attr in entry.get("attributes", []):
            if attr.get("trait_type") == "Token ID":
                return int(attr.get("value", 0))
        return 0
    except Exception:
        return 0

def start_ssh_agent():
    result = subprocess.run(["ssh-agent", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    for line in output.splitlines():
        if "SSH_AUTH_SOCK" in line or "SSH_AGENT_PID" in line:
            key, value = line.split(";", 1)[0].split("=", 1)
            os.environ[key] = value
    ssh_key_path = os.path.expanduser("~/id_rsa.pub")  # Use private key, not .pub
    subprocess.run(["ssh-add", ssh_key_path], check=True)

def git_workflow(commit_message="Auto commit"):
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=False)
    subprocess.run(["git", "push"], check=True)

from eth_account import Account

def generate_evm_address():
    acct = Account.create()
    return acct.address

if __name__ == '__main__':
    app.run(debug=True)