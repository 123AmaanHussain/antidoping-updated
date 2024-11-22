// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract AntidopingCertificate is ERC721, ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    // Certificate metadata structure
    struct Certificate {
        string quizTitle;
        uint256 score;
        string date;
        address recipient;
        string ipfsHash;
        uint256 timestamp;
        bool isRevoked;
    }

    // Mapping from token ID to Certificate
    mapping(uint256 => Certificate) private _certificates;
    
    // Mapping from owner to their token IDs
    mapping(address => uint256[]) private _ownerTokens;
    
    // Events
    event CertificateMinted(
        uint256 indexed tokenId,
        address indexed recipient,
        string quizTitle,
        uint256 score,
        string date,
        string ipfsHash,
        uint256 timestamp
    );
    
    event CertificateRevoked(uint256 indexed tokenId, string reason);
    event CertificateUpdated(uint256 indexed tokenId, string ipfsHash);

    constructor() ERC721("Antidoping Certificate", "ADPC") {}

    function mintCertificate(
        address recipient,
        string memory quizTitle,
        uint256 score,
        string memory date,
        string memory ipfsHash
    ) public onlyOwner returns (uint256) {
        require(recipient != address(0), "Invalid recipient address");
        require(bytes(quizTitle).length > 0, "Quiz title cannot be empty");
        require(score <= 100, "Score must be between 0 and 100");

        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _safeMint(recipient, newTokenId);
        
        // Store certificate data
        _certificates[newTokenId] = Certificate({
            quizTitle: quizTitle,
            score: score,
            date: date,
            recipient: recipient,
            ipfsHash: ipfsHash,
            timestamp: block.timestamp,
            isRevoked: false
        });
        
        // Add token to owner's collection
        _ownerTokens[recipient].push(newTokenId);
        
        // Emit event
        emit CertificateMinted(
            newTokenId,
            recipient,
            quizTitle,
            score,
            date,
            ipfsHash,
            block.timestamp
        );

        return newTokenId;
    }

    function getCertificate(uint256 tokenId) public view returns (
        string memory quizTitle,
        uint256 score,
        string memory date,
        address recipient,
        string memory ipfsHash
    ) {
        require(_exists(tokenId), "Certificate does not exist");
        Certificate storage cert = _certificates[tokenId];
        require(!cert.isRevoked, "Certificate has been revoked");
        
        return (
            cert.quizTitle,
            cert.score,
            cert.date,
            cert.recipient,
            cert.ipfsHash
        );
    }

    function getCertificatesByOwner(address owner) public view returns (uint256[] memory) {
        return _ownerTokens[owner];
    }

    function updateCertificateIPFS(uint256 tokenId, string memory newIpfsHash) public onlyOwner {
        require(_exists(tokenId), "Certificate does not exist");
        require(!_certificates[tokenId].isRevoked, "Certificate has been revoked");
        
        _certificates[tokenId].ipfsHash = newIpfsHash;
        emit CertificateUpdated(tokenId, newIpfsHash);
    }

    function revokeCertificate(uint256 tokenId, string memory reason) public onlyOwner {
        require(_exists(tokenId), "Certificate does not exist");
        require(!_certificates[tokenId].isRevoked, "Certificate already revoked");
        
        _certificates[tokenId].isRevoked = true;
        emit CertificateRevoked(tokenId, reason);
    }

    function isRevoked(uint256 tokenId) public view returns (bool) {
        require(_exists(tokenId), "Certificate does not exist");
        return _certificates[tokenId].isRevoked;
    }

    function getCertificateTimestamp(uint256 tokenId) public view returns (uint256) {
        require(_exists(tokenId), "Certificate does not exist");
        return _certificates[tokenId].timestamp;
    }

    // Override required functions
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
