// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract FUNNFT is ERC721URIStorage, Ownable {
    using Strings for uint256;

    uint256 public nextTokenId;
    string public baseTokenURI;

    event Minted(address indexed to, uint256 indexed tokenId, string tokenURI, string title, string description);

    constructor(string memory baseURI_, address initialOwner) ERC721("FUN_NFT", "FUNNFT") Ownable(initialOwner) {
        baseTokenURI = baseURI_;
    }

    /**
     * @dev Anyone can mint a FUN_NFT to any address by paying the gas cost.
     * @param to The address to receive the NFT.
     * @param title The title of the NFT.
     * @param description The description of the NFT.
     */
    function mint(address to, string memory title, string memory description) external returns (uint256) {
        uint256 tokenId = nextTokenId++;
        _safeMint(to, tokenId);

        // Avoid unnecessary string conversion by using abi.encodePacked directly
        string memory metadataURI = string(abi.encodePacked(baseTokenURI, Strings.toString(tokenId), ".json"));
        _setTokenURI(tokenId, metadataURI);

        emit Minted(to, tokenId, metadataURI, title, description);
        return tokenId;
    }

    function getBaseTokenURI() external view returns (string memory) {
        return baseTokenURI;
    }

    function setBaseURI(string memory newBaseURI) external onlyOwner {
        baseTokenURI = newBaseURI;
    }
}