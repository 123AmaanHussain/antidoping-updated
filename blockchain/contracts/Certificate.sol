// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract AntidopingCertificate is ERC721 {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    struct CertificateData {
        string quizTitle;
        uint256 score;
        string date;
        address recipient;
        string ipfsHash;  // Store additional metadata on IPFS
    }

    mapping(uint256 => CertificateData) public certificates;

    event CertificateMinted(
        uint256 indexed tokenId,
        address indexed recipient,
        string quizTitle,
        uint256 score,
        string date
    );

    constructor() ERC721("Antidoping Certificate", "ADPC") {}

    function mintCertificate(
        address recipient,
        string memory quizTitle,
        uint256 score,
        string memory date,
        string memory ipfsHash
    ) public returns (uint256) {
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _safeMint(recipient, newTokenId);

        certificates[newTokenId] = CertificateData(
            quizTitle,
            score,
            date,
            recipient,
            ipfsHash
        );

        emit CertificateMinted(newTokenId, recipient, quizTitle, score, date);

        return newTokenId;
    }

    function getCertificate(uint256 tokenId) public view returns (CertificateData memory) {
        require(_exists(tokenId), "Certificate does not exist");
        return certificates[tokenId];
    }

    function getCertificatesByOwner(address owner) public view returns (uint256[] memory) {
        uint256 balance = balanceOf(owner);
        uint256[] memory result = new uint256[](balance);
        uint256 counter = 0;
        
        for (uint256 i = 1; i <= _tokenIds.current(); i++) {
            if (_exists(i) && ownerOf(i) == owner) {
                result[counter] = i;
                counter++;
            }
        }
        
        return result;
    }
}
