// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract CPUBToken is ERC20, Ownable {
    uint256 private constant ONE = 1;
    uint256 private constant TEN = 10;
    uint256 private constant HUNDRED = 100;

    constructor(address initialOwner) ERC20("CPUB Token", "CPUB") Ownable(initialOwner) {}

    /**
     * @dev Mint 1, 10, or 100 CPUB tokens to a specified address.
     * Only the owner can call this function.
     */
    function mintTo(address to, uint256 amount) external onlyOwner {
        require(
            amount == ONE || amount == TEN || amount == HUNDRED,
            "Amount must be 1, 10, or 100 CPUB"
        );
        _mint(to, amount);
    }

    function decimals() public pure override returns (uint8) {
        return 0;
    }
}