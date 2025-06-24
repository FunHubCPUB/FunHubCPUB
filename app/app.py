import uuid
from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import subprocess
from web3 import Web3
import json
from dotenv import load_dotenv
load_dotenv()
from werkzeug.utils import secure_filename
import urllib.parse

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_image(image_url):
    if image_url.startswith("https"):
        # Ensure images directory exists
        os.makedirs("images", exist_ok=True)

        # Extract filename from URL
        parsed_url = urllib.parse.urlparse(image_url)
        filename = os.path.basename(parsed_url.path).replace(":", "_")  # Replace colon for valid filenames
        filepath = os.path.join("images", filename )  # Adjust extension if needed
        link = "https://funhub.lol/app/images/"+filename
        # Use curl in subprocess to download the image
        try:
            subprocess.run(["curl", "-o", filepath, image_url], check=True)
            print(f"Image saved as {filepath}")
            return link
        except subprocess.CalledProcessError as e:
            print(f"Download failed: {e}")
    else:
        print("Invalid URL: must start with https")
app = Flask(__name__)
UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load private key for minting (should be the owner's key)
# Add variables to a .env file in this directory
OWNER_ADDRESS = Web3.to_checksum_address(os.getenv('WALLET_ADDRESS'))
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
FUNNFT_ADDRESS = os.getenv('FUNNFT_ADDRESS')  # Set this in your .env or config
CELO_RPC = os.getenv("CELO_RPC")
RSA_LOCATION=os.getenv("RSA_LOCATION")
app.secret_key = os.getenv("SECRET_KEY")
CPUB_ADDRESS = os.getenv('CPUB_ADDRESS')

# Connect to Celo (or your preferred network)
w3 = Web3(Web3.HTTPProvider(CELO_RPC))

# Load ABI and contract address
FUNNFT_ABI_PATH = os.path.join(os.path.dirname(__file__), 'funnft_abi.json')
# Load contract ABI
with open(FUNNFT_ABI_PATH, 'r') as abi_file:
    funnft_abi = json.load(abi_file)
funnft_contract = w3.eth.contract(address=Web3.to_checksum_address(FUNNFT_ADDRESS), abi=funnft_abi)

CPUB_ABI_PATH = os.path.join(os.path.dirname(__file__), 'cpub_abi.json')
with open(CPUB_ABI_PATH, 'r') as abi_file:
    cpub_abi = json.load(abi_file)
cpub_contract = w3.eth.contract(address=Web3.to_checksum_address(CPUB_ADDRESS), abi=cpub_abi)

# Directory setup
current_dir = os.getcwd()
OUTPUT_DIR = os.path.join(current_dir, 'html')
JSON_DIR = os.path.join(current_dir, 'metadata')
GITHUB_REPO_DIR = os.path.abspath(os.path.join(current_dir, os.pardir))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            flash("Please use your wallet address to login.")
        elif 'wallet_address' in request.json:
            wallet_address = request.json['wallet_address']
            if Web3.is_address(wallet_address):
                session['logged_in'] = True
                session['wallet_address'] = Web3.to_checksum_address(wallet_address.lower())
                return {"status": "success", "message": "Wallet verified successfully!"}, 200
            else:
                return {"status": "error", "message": "Invalid wallet address!"}, 400
    return render_template('login.html')
def starts_with_https(url):
    return url.startswith('https://')

@app.route('/editor', methods=['GET', 'POST'])
def editor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        username = request.form['username']
        wallet_address = request.form.get('wallet_address') or session.get('wallet_address')

        # 🔽 Handle File Upload
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = 'https://funhub.lol/app/images/'+filename
        else:
            image_url = "https://funhub.lol/app/images/TVRjeE1UQXlNVFUzT0E9PV8xNDM2.jpg"

        # 🪙 Mint NFT
        tx_hash, gas_fee_eth, receipt, token_id, cpub_tx_hash = mint_and_return_receipt(title, body)

        if not tx_hash:
            flash("NFT minting failed.")
            return redirect(url_for('editor'))

        # 📦 JSON Metadata
        json_content = {
            "name": title,
            "description":image_url+" \r\n \r\n "+ body,
            "image": image_url,
            "external_url": f"https://funhub.lol/app/html/{token_id}.html",
            "attributes": [
                {"trait_type": "Creator", "value": username},
                {"trait_type": "Wallet", "value": wallet_address},
                {"trait_type": "Token ID", "value": token_id}
            ]
        }
        with open(os.path.join(JSON_DIR, f"{token_id}.json"), "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)

        # 🧾 HTML Page Generation
        with open(os.path.join(OUTPUT_DIR, f"{token_id}.html"), "w", encoding="utf-8") as f:
            f.write(render_template('page_template.html', image=image_url,
                                    title=title,
                                    body=body,
                                    username=username,
                                    wallet_address=wallet_address,
                                    token_id=token_id))

        # 🔍 NFT Index Page
        nft_entries = []
        for entry in get_json_file_names(JSON_DIR):
            try:
                with open(os.path.join(JSON_DIR, entry), "r", encoding="utf-8") as f:
                    nft_entries.append(json.load(f))
            except Exception as e:
                print(f"Error loading {entry}: {e}")
        nft_entries_sorted = sorted(nft_entries, key=get_token_id, reverse=True)
        with open(os.path.join(current_dir, 'nfts.html'), "w", encoding="utf-8") as f:
            f.write(render_template('nfts.html', entries=nft_entries_sorted))

        # Done
        start_ssh_agent()
        git_workflow("Added "+title)
        return render_template('success.html', tx_hash=tx_hash, gas_fee_eth=gas_fee_eth, receipt=receipt, token_id=token_id, cpub_tx_hash=cpub_tx_hash)

    return render_template('editor.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
def mint_and_return_receipt(title, description):
    """
    Mints a new NFT using the FUNNFT contract and sends 1 CPUB token to the wallet address.
    Returns tx_hash, gas_fee_eth, receipt, token_id, cpub_tx_hash.
    """
    try:
        wallet_address = session.get('wallet_address')
        if not wallet_address or not Web3.is_address(wallet_address):
            raise Exception("Invalid or missing wallet address in session.")

        account = w3.eth.account.from_key(PRIVATE_KEY)

        # Mint NFT to the session wallet_address
        nonce = w3.eth.get_transaction_count(account.address)
        txn = funnft_contract.functions.mint(
            wallet_address,  # send NFT to this address
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

        # Get the tokenId from the Minted event (for reliability)
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
            # fallback: get nextTokenId - 1
            token_id = funnft_contract.functions.nextTokenId().call()
        if not wallet_address or not Web3.is_address(wallet_address):
            raise Exception("Invalid or missing wallet address in session.")
        # Mint 1 CPUB token to the wallet address (no decimals, only 1, 10, or 100 allowed)
        cpub_txn = cpub_contract.functions.mintTo(wallet_address, 1).build_transaction({
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

def get_html_file_names(directory):
    """
    Get the names of all .html files in the specified directory.
    """
    if not os.path.exists(directory):
        return []
    return [file for file in os.listdir(directory) if file.endswith('.html')]

def get_json_file_names(directory):
    """
    Get the names of all .html files in the specified directory.
    """
    if not os.path.exists(directory):
        return []
    return [file for file in os.listdir(directory) if file.endswith('.json')]

def get_attribute(attributes, trait_type):
    for attr in attributes:
        if attr.get("trait_type") == trait_type:
            return attr.get("value")
    return None

app.jinja_env.globals.update(get_attribute=get_attribute)

def get_token_id(entry):
    try:
        return int(get_attribute(entry["attributes"], "Token ID") or 0)
    except Exception:
        return 0

import os
import subprocess

def start_ssh_agent():
    # Start the SSH agent
    result = subprocess.run(["ssh-agent", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    for line in output.splitlines():
        if "SSH_AUTH_SOCK" in line or "SSH_AGENT_PID" in line:
            key, value = line.split(";", 1)[0].split("=", 1)
            os.environ[key] = value

    # Add the SSH private key (assuming ~/.rsa_id is the corresponding private key)
    ssh_key_path = os.path.expanduser("~/id_rsa.pub") #Private key, not .pub
    subprocess.run(["ssh-add", ssh_key_path], check=True)

def git_workflow(commit_message="Auto commit"):
    # Stage all changes
    subprocess.run(["git", "add", "."], check=True)

    # Commit with a message
    subprocess.run(["git", "commit", "-m", commit_message], check=False)

    # Push to remote
    subprocess.run(["git", "push"], check=True)


if __name__ == '__main__':
    app.run(debug=True)