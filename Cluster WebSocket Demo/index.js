let cluster = require('cluster');
let WebSocket = require('ws');

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
function getUniqueStr() {
  let macAddress = genMAC();
  while (tempSet.has(macAddress)) {
    macAddress = genMAC();
  }
  tempSet.add(macAddress);
  return macAddress;
}

var sendMsg = { "msg_type": 512, "mac": "D0-B0-76-46-1A-C0", "id": "", "user_name": "${__UUID}", "softwares": [{ "name": "电脑2", "version": "", "id": "", "date": "2020-05-15", "type": "av" }] };

var iniMsg = { "msg_type": 1, "mac_list": null, "version": "2" };

if (cluster.isMaster) {
  console.log(`[master] start master...`);
  for (let x of Array(200)) {
    const worker = cluster.fork();
    worker.send(getUniqueStr());

    worker.on('message', workerId => setTimeout(() => worker.kill(), 5000));
  }
  cluster.on('exit', (worker, code, signal) => console.log(`[worker] ${worker.id} died`));
} else if (cluster.isWorker) {
  console.log(`[worker] start worker... ${cluster.worker.id}`);
  process.on('message', macAddress => {
    createWs(macAddress);
    process.send(cluster.worker.id);
  });
}

function createWs(macAddress) {
  var ws = new WebSocket("ws://192.168.0.168:8007/"); //申请一个WebSocket对象，参数是服务端地址，同http协议使用http://开头一样，WebSocket协议的url使用ws://开头，另外安全的WebSocket协议使用wss://开头
  ws.onopen = function () { //当WebSocket创建成功时，触发onopen事件
    // console.log(`[worker] macAddress: ${macAddress}`);
    // sendMsg.mac = macAddress;
    // ws.send(JSON.stringify(sendMsg)); //将消息发送到服务端
    ws.send(JSON.stringify(iniMsg));
  }

  ws.onmessage = function (e) { //当客户端收到服务端发来的消息时，触发onmessage事件，参数e.data包含server传递过来的数据
    console.log(`[worker] macAddress: ${macAddress}`);
    sendMsg.mac = macAddress;
    ws.send(JSON.stringify(sendMsg)); //将消息发送到服务端
    console.log(e.data);
  }

  ws.onclose = function (e) { //当客户端收到服务端发送的关闭连接请求时，触发onclose事件
    console.log("close");
  }

  ws.onerror = function (e) {
    //如果出现连接、处理、接收、发送数据失败的时候触发onerror事件
    console.log(e);
  }
  return ws;
}