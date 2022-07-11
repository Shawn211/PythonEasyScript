const fs = require('fs');
const path = require('path');

// 生成 mac 地址数量
const macNum = 200;

function genMAC() {
  var hexDigits = "123456789ABCDEF";
  var macAddress = "";
  for (var i = 0; i < 6; i++) {
    macAddress += hexDigits.charAt(Math.round(Math.random() * 15));
    macAddress += hexDigits.charAt(Math.round(Math.random() * 15));
    if (i != 5) macAddress += "-";
  }

  return macAddress;
}

let tempSet = new Set();
const macFilenames = fs.readdirSync(__dirname).filter(filename => /\d{13}\.json/.test(filename));
for (let macFilename of macFilenames) {
  let { mac_list } = JSON.parse(fs.readFileSync(macFilename));
  for (let mac of mac_list) {
    tempSet.add(mac);
  }
}

function getUniqueStr() {
  let macAddress = genMAC();
  while (tempSet.has(macAddress)) {
    macAddress = genMAC();
  }
  tempSet.add(macAddress);
  return macAddress;
}

let mac_list = [];
for (let index of Array(macNum)) {
  mac_list.push(getUniqueStr());
}
const macFilename = `${new Date().getTime().toString()}.json`;
fs.writeFileSync(macFilename, JSON.stringify({ mac_list }));
const clusterConnectorDemoJSString = fs.readFileSync('clusterConnectorDemo.js', { encoding: 'utf-8' });
const newClusterConnectorDemoJSString = clusterConnectorDemoJSString.replace(/(?<=const macFilename \= ')(\d{13}\.json)?(?=';)/, macFilename);
fs.writeFileSync(`clusterConnector${macFilenames.length}.js`, newClusterConnectorDemoJSString);