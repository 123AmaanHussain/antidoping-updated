const AntidopingCertificate = artifacts.require("AntidopingCertificate");

module.exports = function(deployer) {
  deployer.deploy(AntidopingCertificate);
};
